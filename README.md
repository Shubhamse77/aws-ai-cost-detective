# 🔍 AWS AI Cloud Cost Detective

[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

An automated multi-region FinOps audit engine for AWS. **AWS AI Cloud Cost Detective** scans **all enabled AWS regions** for idle, orphaned, or over-provisioned infrastructure, calculates exact monthly dollar waste, and leverages AI (Amazon Bedrock / Fallback Rule Engine) to generate risk-evaluated remediation plans and ready-to-run AWS CLI commands.

---

## 🌟 Key Features

* **🌍 Dynamic Multi-Region Scanning:** Automatically detects and audits all active/enabled AWS regions in your account concurrently using multi-threading.
* **💸 Comprehensive Waste Detection:**
  * **Unattached EBS Volumes:** Identifies volumes sitting in `available` state.
  * **Stale Snapshots:** Finds snapshots older than $N$ days without active references.
  * **Unassigned Elastic IPs:** Uncovers allocated EIPs incurring hourly charges without compute attachments.
  * **Stopped & Underutilized EC2s:** Detects stopped instances holding storage and low-CPU instances ($<5\%$ average utilization).
  * **Idle Load Balancers:** Flags ALBs/NLBs with 0 target instances attached.
* **📊 Cost Explorer Integration:** Pulls historical 30-day account spend and breaks down costs per service.
* **🤖 AI Reasoning & Risk Assessment:** Categorizes waste into `LOW_RISK`, `MEDIUM_RISK`, and `HIGH_RISK` levels, pairing each with explicit monthly savings estimates.
* **⚡ Streamlit Interactive Dashboard:** Clean web UI to execute audits with a single click and view/copy ready-to-use cleanup CLI commands.

---

## 🏗️ Architecture Overview

```text
               ┌─────────────────────────────────────────┐
               │    AWS Multi-Region Infrastructure      │
               └────────────────────┬────────────────────┘
                                    │
                         (Concurrent Boto3 Scanners)
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │                 Multi-Region Scanner Engine            │
       │   - EBS Scanner (Unattached Volumes & Stale Snapshots) │
       │   - EIP Scanner (Unallocated Public IPs)               │
       │   - EC2 Scanner (Stopped & Low CPU Utilization)        │
       │   - ALB Scanner (Idle Load Balancers)                  │
       └────────────────────────────┬───────────────────────────┘
                                    │
                        (Consolidated JSON Findings)
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │             AWS Cost Explorer & Estimator              │
       │   - Queries 30-Day Account Spend via Cost Explorer API  │
       │   - Attaches $ Monthly Waste Estimates per Resource    │
       └────────────────────────────┬───────────────────────────┘
                                    │
                          (Master Data Payload)
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │               AI Reasoning & Fix Engine                │
       │   - Risk Scoring (LOW / MEDIUM / HIGH)                 │
       │   - Generates Safe Execution AWS CLI Commands          │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │   Streamlit Web Dashboard │
                      └───────────────────────────┘
```
---

## 📋 Prerequisites

**Python 3.10+** installed on your machine.

**AWS CLI installed** and configured with valid credentials (aws configure).

**IAM Permissions**: The configured IAM user/role requires read-only permissions for EC2, ELBv2, CloudWatch, and Cost Explorer:

create an role with the following policy (Read-Only access to costs and resources):
and attach that role to EC2 

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostExplorerAndRegions",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetDimensionValues",
        "ec2:DescribeRegions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ResourceScannersReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "cloudwatch:GetMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```
---

## 🚀 Getting Started
### 1. Clone the Repository
```bash
git clone https://github.com/Shubhamse77/aws-ai-cost-detective
cd aws-ai-cost-detective
```
---
### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows (PowerShell)
# .\venv\Scripts\Activate.ps1
```
---
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
---
### 4. Environment Configuration
Create a .env file in the root directory:
```bash
vim .env
```
---
Configure your parameters inside .env:

```bash
AWS_DEFAULT_REGION=us-east-1

# Choices: fallback, bedrock, openai, gemini
LLM_PROVIDER=fallback

# Bedrock Model (If LLM_PROVIDER=bedrock)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```
---
### 💻 Usage
### Run via Interactive Streamlit Web UI
Launch the Streamlit web dashboard locally:

```bash
streamlit run app.py
```
Open your browser at http://localhost:8501, click 🚀 Run Multi-Region Cost Audit in the sidebar, and inspect the interactive risk breakdown, regional findings, and AI remediation plan.
