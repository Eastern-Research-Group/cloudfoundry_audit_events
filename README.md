# Cloud Foundry Audit Events

This repository contains a script and associated GitHub Action that can be used to automatically export [Cloud Foundry Audit Events](https://docs.cloudfoundry.org/running/managing-cf/audit-events.html) on a scheduled basis. It also contains a script that can create an MS Excel document based on the data obtained from the automated script.

Notice: The latest version of this script (2024-01-14) contains breaking command-line parameter name changes which aligns the naming convention better with other scripts (specifically with the new organization and space name parameters).  

Also, please note: There is an external sister repository ([cloudfoundry_auditing_scripts](https://github.com/Eastern-Research-Group/cloudfoundry_auditing_scripts)) that has many other helpful Cloud Foundry related scripts.

## Reason for its creation

The Cloud Foundry instance we're using (cloud.gov) is only setup to retain [Cloud Foundry Audit Events](https://docs.cloudfoundry.org/running/managing-cf/audit-events.html) for 31 days. Based on this, we needed a way to make sure audit events were being exported and saved elsewhere before they expired. While our configuration of the GitHub Action is currently setup to run every 24 hours, other users can easily adjust it to suit their needs. The script is smart enough to know when it last ran to make sure all events are captured and not duplicated. 

## Initial goals

 - Automate Cloud Foundry Audit Event extraction to support auditing and archiving requirements.
 - Make the code simple to understand to instill trust in its usage.
 - Avoid using 3rd party dependencies if possible (i.e., focus on using base Python features).
 - Provide a solution that can be easily enhanced as time allows.
 - Ensure audit event data is not lost or duplicated.
 - Make it easy for auditors to review the audit events.
 
## Suggested steps to setup

 1. Copy this code into a private GitHub repository you own.
 2. Configure the GitHub Action schedule setting (located in the GitHub Action .yml) to match your requirement. The default is set to run every 24 hours. Information on changing the schedule can be found [here](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule).
 3. Setup the the two required Action Secrets ( *CG_USERNAME* and *CG_PASSWORD*). The values for these secrets are explained [here](https://cloud.gov/docs/services/cloud-gov-service-account/). For help setting up Action Secrets, see [Set up Secrets in GitHub Action workflows](https://github.com/Azure/actions-workflow-samples/blob/master/assets/create-secrets-for-GitHub-workflows.md). 

## Repository structure once the GitHub Action executes

<p align="center">
      <img height="100%" width="100%" src="/docs/img/folder_tree.png" alt="Screenshot of repo folder structure after GitHub Action execution">
</p>

## How to create an audit report (i.e., MS Excel based)

 Navigate to the scripts folder and execute the *audit_event_reporter.py* script. A usage example is below:

**Example:**

python audit_event_reporter.py -i C:\Cooper\cloudfoundry_audit_events\data\test-org\events\2021-12.json -o C:\Cooper\Desktop\AuditReport-2021-12.xlsx

**Usage**
 - **input_file** - file path to the .json file holding audit events created but the GitHub Action.
 - **organization** - (optional) The organization name to filter results by.
 - **spaces** - (optional) A comma delimited string of space names to filter the results by.
 - **event_begin_dt** - (optional) Begin date for which events should include in the output report file.
 - **event_end_dt** - (optional) End date for which events should include in the output report file.
 - **report_file** - file path to where to save the MS Excel based results to.

## Disclaimer

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.
