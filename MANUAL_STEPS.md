# Manual Configuration Steps for Logic App Reporting Workflow

After applying the Terraform configuration, follow these steps to finalize the Logic App setup.

## 1. Import the Workflow Definition
1. Navigate to the **Logic App (Consumption)** resource (`logic-base-project-reporting`) in the Azure Portal.
2. Go to **Logic App Designer**.
3. If prompted with a template selection, you can choose "Blank Logic App", but verify you are in the designer.
4. Click on **Code View** (top menu).
5. Copy the content of `scripts/logic_app_workflow.json` from this repository.
6. Paste it into the Code View, replacing the existing JSON content.
7. **Save** the workflow.

## 2. Configure Connections
The designer will likely show errors because the API connections (Blob Storage and Communication Services) need to be linked or authorized.

1. Switch to **Designer** view.
2. **Azure Blob Storage (Get blob content)**:
   - Click on the action.
   - It should show the existing connection `azureblob-connection` (created by Terraform).
   - If it shows an error "Invalid connection", click "Change connection" and select `azureblob-connection`.
   - You might need to **Authorize** or re-authenticate the connection if prompted (Managed Identity should work automatically, but sometimes requires a click).
   - In the action parameters:
     - **Blob path**: Ensure the expression `split(triggerBody()?['data']?['url'], '.net/')[1]` is preserved.
     - **Storage Account Name**: Enter the name of the storage account (`stbaseprojectrpt...`).

3. **Azure Communication Services (Send email)**:
   - Click on the action.
   - It will ask you to create a connection (as Terraform did not create this one).
   - Choose **Azure Communication Services**.
   - Authentication Type: **Logic App Managed Identity** (if supported) or **Connection String** (you can get this from the ACS resource).
   - Connection Name: `acs-connection`.
   - Click **Create**.
   - In the action parameters:
     - **From**: Update `DoNotReply@<YOUR_DOMAIN_HERE>` with your actual MailFrom address (e.g., `DoNotReply@<your-guid>.azurecomm.net`). You can find this in the "Email Communication Service" -> "Provision domains".
     - **To**: Update `replace_me@example.com` with the desired recipient email.
     - **Subject**: "New Monthly Report".
     - **Body**: Verify the content.
     - **Attachments**: Ensure `Report.xlsx` is set with content `@{base64(body('Get_blob_content_(V2)'))}`.

4. **Save** the workflow again.

## 3. Get the Webhook URL
1. Once saved, expand the **When a resource event occurs** trigger.
2. Copy the **HTTP POST URL**.

## 4. Create the Event Grid Subscription
1. Navigate to the **Event Grid System Topic** resource (`egst-logic-base-project-reporting`) in the Resource Group `rg-base-project-reporting`.
2. Click **+ Event Subscription**.
3. **Name**: `sub-send-report-email`.
4. **Event Schema**: Event Grid Schema.
5. **Topic Details**: Should already be filled.
6. **Event Types**: Filter to **Blob Created** (`Microsoft.Storage.BlobCreated`).
7. **Endpoint Type**: Select **Web Hook**.
8. **Endpoint**: Click "Select an endpoint" and paste the **HTTP POST URL** you copied from the Logic App.
9. Click **Create**.

## 5. Test
1. Manually upload a file to the `reports` container in the storage account.
2. Check the **Logic App** run history to see if it triggered and sent the email.
