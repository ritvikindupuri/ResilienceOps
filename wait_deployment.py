import boto3, time, sys

ssm = boto3.client("ssm", region_name="us-east-1")
cmd_id = "4bdfe1a6-aaea-4314-afb3-1776fb76890d"
instance_id = "i-0cf1c979f2cbd01c4"

for i in range(24):
    try:
        res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
        status = res["Status"]
        print(f"[{i*5}s] Deployment Status: {status}")
        if status in ["Success", "Failed", "Cancelled", "TimedOut"]:
            print("Standard Output:\n", res.get("StandardOutputContent", "")[-1500:])
            if status != "Success":
                print("Error Output:\n", res.get("StandardErrorContent", "")[-1500:])
            break
    except Exception as e:
        print("Waiting for invocation record...", e)
    time.sleep(5)
