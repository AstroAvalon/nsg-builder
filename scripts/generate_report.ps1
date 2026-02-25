try {
    # 1. Connect to Azure
    Write-Output "Connecting to Azure..."
    Disable-AzContextAutosave -Scope Process
    Connect-AzAccount -Identity

    # 2. Get Configuration
    try {
        $StorageAccountName = Get-AutomationVariable -Name "ReportStorageAccountName"
    }
    catch {
        Write-Error "Failed to retrieve Automation Variable 'ReportStorageAccountName'. Ensure it is defined."
        throw $_
    }

    if (-not $StorageAccountName) {
        throw "Automation Variable 'ReportStorageAccountName' is empty."
    }
    Write-Output "Target Storage Account: $StorageAccountName"

    # 3. Gather Subnet Data
    Write-Output "Gathering Subnet Information..."
    $SubnetData = @()
    $VNets = Get-AzVirtualNetwork
    foreach ($VNet in $VNets) {
        foreach ($Subnet in $VNet.Subnets) {
            $Prefix = $Subnet.AddressPrefix
            if (-not $Prefix) {
                $Prefix = $Subnet.AddressPrefixes -join ", "
            }

            $SubnetData += [PSCustomObject]@{
                VNetName      = $VNet.Name
                SubnetName    = $Subnet.Name
                AddressPrefix = $Prefix
                Location      = $VNet.Location
                ResourceGroup = $VNet.ResourceGroupName
            }
        }
    }

    # 4. Gather Storage Data
    Write-Output "Gathering Storage Information..."
    $StorageData = @()
    $StorageAccounts = Get-AzStorageAccount
    foreach ($SA in $StorageAccounts) {
        $UsedCapacity = 0
        try {
            # Get UsedCapacity metric (latest available)
            # TimeGrain 1h is standard for metrics
            $Metric = Get-AzMetric -ResourceId $SA.Id -MetricName "UsedCapacity" -TimeGrain "01:00:00" -WarningAction SilentlyContinue

            if ($Metric.Data.Count -gt 0) {
                $UsedCapacity = $Metric.Data[-1].Average
            }
        }
        catch {
            Write-Warning "Could not retrieve metrics for $($SA.StorageAccountName): $_"
        }

        $StorageData += [PSCustomObject]@{
            StorageAccountName = $SA.StorageAccountName
            ResourceGroup      = $SA.ResourceGroupName
            Location           = $SA.Location
            SkuName            = $SA.Sku.Name
            UsedCapacityBytes  = $UsedCapacity
            UsedCapacityGB     = [math]::Round($UsedCapacity / 1GB, 4)
        }
    }

    # 5. Generate Excel
    $ReportFileName = "AzureReport_$(Get-Date -Format 'yyyyMMdd_HHmm').xlsx"
    $ReportPath = Join-Path $env:TEMP $ReportFileName
    Write-Output "Generating Excel Report at $ReportPath..."

    # Ensure ImportExcel is available (Auto-loading should work if installed)
    if (-not (Get-Module -ListAvailable -Name ImportExcel)) {
        throw "Module 'ImportExcel' is not available."
    }

    $SubnetData | Export-Excel -Path $ReportPath -WorksheetName "Subnets" -AutoSize -AutoFilter
    $StorageData | Export-Excel -Path $ReportPath -WorksheetName "Storage" -AutoSize -AutoFilter

    # 6. Upload to Storage
    Write-Output "Uploading report to container 'reports' in $StorageAccountName..."

    # Create context using Managed Identity
    $Context = New-AzStorageContext -StorageAccountName $StorageAccountName -UseConnectedAccount

    # Check if container exists, if not create it (though TF should have done it)
    if (-not (Get-AzStorageContainer -Name "reports" -Context $Context -ErrorAction SilentlyContinue)) {
        Write-Warning "Container 'reports' not found. Attempting to create..."
        New-AzStorageContainer -Name "reports" -Context $Context -Permission Off
    }

    Set-AzStorageBlobContent -File $ReportPath -Container "reports" -Context $Context -Blob $ReportFileName -Force

    Write-Output "Report generation and upload completed successfully."
}
catch {
    Write-Error "An error occurred: $_"
    throw $_
}
