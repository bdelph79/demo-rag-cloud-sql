
https://codelabs.developers.google.com/codelabs/cloud-db-retrieval-app?hl=en#3

pwd: 2301b4d13527ddbec2cbce84

git clone https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app.git 

export CLOUD_SQL_MYSQL_PROJECT=dataweb
export CLOUD_SQL_MYSQL_REGION=us-central1
export CLOUD_SQL_MYSQL_INSTANCE=my-cloudsql-instance
export CLOUD_SQL_MYSQL_DATABASE=assistantdemo
export CLOUD_SQL_MYSQL_USER=root
export CLOUD_SQL_MYSQL_PASSWORD=2301b4d13527ddbec2cbce84


# 1. Download the latest binary (using v0.21.0 as a stable baseline)
export VERSION=0.21.0
curl -L -o toolbox "https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox"

# 2. Make it executable
chmod +x toolbox

# 3. Verify it works
./toolbox --version



This command fails because the toolbox binary is not pre-installed in the standard Google Cloud Shell environment. You are likely following a guide (like the Gemini Code Assist or MCP setup) that assumes you have already downloaded this specific tool.

To get this running, you need to download the MCP Toolbox for Databases binary, set the required environment variables, and then run it.

Step 1: Download and Install the Toolbox
Run the following commands in your Cloud Shell to download the latest Linux binary and make it executable.

Bash

# 1. Download the latest binary (using v0.21.0 as a stable baseline)
export VERSION=0.21.0
curl -L -o toolbox "https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox"

# 2. Make it executable
chmod +x toolbox

# 3. Verify it works
./toolbox --version
Step 2: Configure Environment Variables
The command ./toolbox --prebuilt cloud-sql-mysql relies on environment variables to know which database to connect to. You must export these before running the command.

Copy and paste this into Cloud Shell, replacing the placeholders with your actual values:

Bash

export CLOUD_SQL_MYSQL_PROJECT="YOUR_PROJECT_ID"
export CLOUD_SQL_MYSQL_REGION="us-central1"       # e.g., us-central1
export CLOUD_SQL_MYSQL_INSTANCE="YOUR_INSTANCE_ID"
export CLOUD_SQL_MYSQL_DATABASE="YOUR_DB_NAME"
export CLOUD_SQL_MYSQL_USER="YOUR_DB_USER"         # Optional if using IAM
export CLOUD_SQL_MYSQL_PASSWORD="YOUR_DB_PASSWORD" # Optional if using IAM
Step 3: Run the Command
Now you can run the command. However, note that this tool is designed to be spoken to by an AI agent (like Gemini or an IDE extension), not a human typing in a terminal.

If you are setting up an IDE Extension (VS Code, Cursor, etc.): You don't run this in Cloud Shell. You download the binary to your local machine, and put the path to it in your IDE's config file.

If you want to test it in Cloud Shell: You can run it, but it will likely just start a server process and "hang" (wait for connections) or expect input via STDIN (if --stdio is added).

Bash

# Starts the server (usually on port 5000 or waits for input)
./toolbox --prebuilt cloud-sql-mysql


Recommended: Using it with the Gemini CLI
If your goal is to chat with your database in Cloud Shell (e.g., "Show me the users table"), you should use the Gemini CLI, which wraps this toolbox.

Install Gemini CLI:

Bash

curl -o gemini https://storage.googleapis.com/gemini-cli/release/0.0.10/linux/amd64/gemini
chmod +x gemini
Install the Cloud SQL Extension:

Bash

./gemini extensions install https://github.com/gemini-cli-extensions/cloud-sql-mysql
Start Chatting:

Bash

# Ensure the exports from Step 2 are set, then:
./gemini
Would you like me to help you find your specific Cloud SQL instance connection details (Region/Instance ID)?


===========

bdelph@MacBookPro Demo-RAG-SQL % gcloud config set project dataweb

~/…/Demo-RAG-SQL $ gcloud auth application-default set-quota-project dataweb-480410

PROJECT_ID=$(gcloud config get-value project)


gcloud services enable sqladmin.googleapis.com \
                       compute.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
                       vpcaccess.googleapis.com \
                       aiplatform.googleapis.com \
                       cloudbuild.googleapis.com \
                       artifactregistry.googleapis.com \
                       run.googleapis.com \
                       iam.googleapis.com


                       Create a password
Define password for the default database user. You can define your own password or use a random function to generate one


export CLOUDSQL_PASSWORD=`openssl rand -hex 12`
Note the generated value for the password


echo $CLOUDSQL_PASSWORD= 68ce8da457f7ef288d77f8af

export region=us-central1
gcloud sql instances create my-cloudsql-instance --region=$region --database-version=MYSQL_8_0_36 --database-flags=cloudsql_vector=ON --root-password=$CLOUDSQL_PASSWORD



MySQL
You can enable the cloudsql_vector flag at instance creation. Currently, vector support is offered in MySQL 8.0.36 & 8.0.37.


export region=us-central1
gcloud sql instances create my-cloudsql-instance --region=$region --database-version=MYSQL_8_0_36 --database-flags=cloudsql_vector=ON --root-password=$CLOUDSQL_PASSWORD


gcloud sql databases create assistantdemo --instance=my-cloudsql-instance --project=dataweb-480410



export CLOUD_SQL_MYSQL_PROJECT=dataweb-480410
export CLOUD_SQL_MYSQL_REGION=us-central1
export CLOUD_SQL_MYSQL_INSTANCE=my-cloudsql-instance
export CLOUD_SQL_MYSQL_DATABASE=assistantdemo
export CLOUD_SQL_MYSQL_USER=root
export CLOUD_SQL_MYSQL_PASSWORD=68ce8da457f7ef288d77f8af

 1. Download the latest binary (using v0.21.0 as a stable baseline)
export VERSION=0.21.0
curl -L -o toolbox "https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox"

# 2. Make it executable
chmod +x toolbox

# 3. Verify it works
./toolbox --version


curl -v -L -o toolbox "https://storage.googleapis.com/genai-toolbox/v0.21.0/darwin/amd64/toolbox"


# 1. Correct the instance name
export CLOUD_SQL_MYSQL_INSTANCE=my-cloudsql-instance

# 2. Ensure other variables are still set (just in case)
export CLOUD_SQL_MYSQL_PROJECT=dataweb-480410
export CLOUD_SQL_MYSQL_REGION=us-central1
export CLOUD_SQL_MYSQL_DATABASE=assistantdemo
export CLOUD_SQL_MYSQL_USER=root
# Re-export the password if needed (using the one you generated earlier)
export CLOUD_SQL_MYSQL_PASSWORD=68ce8da457f7ef288d77f8af

# 3. Run the toolbox
./toolbox --prebuilt cloud-sql-mysql


 export CLOUD_SQL_MYSQL_INSTANCE=my-cloudsql-instance
export CLOUD_SQL_MYSQL_PROJECT=dataweb-480410
export CLOUD_SQL_MYSQL_REGION=us-central1
export CLOUD_SQL_MYSQL_DATABASE=assistantdemo
export CLOUD_SQL_MYSQL_USER=root
export CLOUD_SQL_MYSQL_PASSWORD=68ce8da457f7ef288d77f8af
./toolbox --prebuilt cloud-sql-mysql



export CLOUD_SQL_MYSQL_INSTANCE=my-cloudsql-instance
./toolbox --prebuilt cloud-sql-mysql



Prepare Python Environment
To continue we are going to use prepared Python scripts from GitHub repository but before doing that we need to install the required software.

In the GCE VM execute:


sudo apt install -y python3.11-venv git
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip


pip install -r requirements.txt

5. Initialize the Database
While Toolbox is running, open a new terminal and execute the database initialization script. This will populate your database with the Cymbal Air data.

python data/run_database_init.py




Running the Agentic App Demo
Before you begin
Make sure you have setup and initialized your Database.

Make sure you are able to launch Toolbox server.

Make sure you have Python 3.11+ installed

Setting up your Environment
Set up Application Default Credentials:

gcloud auth application-default login
Install the dependencies using pip. You may wish to do this in a virtual environment, e.g. venv:

pip install -r requirements.txt
Tip

If you are running into 403 error, check to make sure the service account you are using has the Cloud Run Invoker IAM in the retrieval service project.

Running the Demo
Start the app with:

python run_app.py
View app in your browser at http://localhost:8081

Tip

For hot reloading, use the --reload flag

python run_app.py --reload`
