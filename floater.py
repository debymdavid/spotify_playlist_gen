import schedule
import time

def test_job():
    print("Job is working!")

schedule.every(1).minute.do(test_job)

print("Schedule module imported successfully!")
print("Testing with a 1-minute job...")

# Run for 3 minutes to test
for i in range(3):
    schedule.run_pending()
    time.sleep(60)