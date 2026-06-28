# Schedule Notification System

## Overview
This is a Telegram-based notification scheduler that ensures 100% delivery by using OpenClaw's `message` tool. It manages scheduled notifications and sends them at the specified time with Korean language support.

## Features
- Schedule registration (time, message, channel)
- Periodic execution for pending notifications
- JSON storage for schedule data
- CLI for add/query/delete operations
- Test mode for verify functionality
- Korean language support with UTF-8 encoding

## Files
- `D:\result\schedule_notifier.py` - Main Python script
- `D:\result\schedule_data.json` - Persistent storage (created automatically)
- `D:\result\pending_messages.json` - Pending messages to be sent (created automatically)
- `D:\result\schedule_log.txt` - Activity logging

## Usage Commands

### Add a notification
```bash
python schedule_notifier.py --add "2026-06-28 15:30" "테스트 메시지" "8616770102"
```

**Arguments:**
- `TIME`: Scheduled time (Format: "YYYY-MM-DD HH:MM" or "HH:MM" - uses today if only HH:MM)
- `MESSAGE`: Notification message content
- `CHANNEL`: Telegram channel/user ID

### List notifications
```bash
python schedule_notifier.py --list
```

### Remove notification
```bash
python schedule_notifier.py --remove <ID>
```

### Run scheduler (for cron)
```bash
python schedule_notifier.py --run
```

### Send test message
```bash
python schedule_notifier.py --test
```

## Integration with OpenClaw
This script works with OpenClaw's `message` tool for guaranteed delivery:

1. When using `--run`, the script writes pending messages to `pending_messages.json`
2. OpenClaw reads from this file and sends messages using the `message` tool
3. After successful delivery, messages are marked as "sent"

### Example OpenClaw Command
```bash
message channel=telegram:direct:8616770102 text='스케줄 알림 메시지'
```

## Cron Setup
Add to crontab (Windows Task Scheduler also works):

```bash
# Every minute to check for pending messages
* * * * * cd /path/to/script && python schedule_notifier.py --run

# Every 5 minutes for more frequent checks
*/5 * * * * cd /path/to/script && python schedule_notifier.py --run
```

## Requirements
- Python 3.6+
- Standard library only (no external dependencies)
- Write permissions to D:\result\ directory

## Support
- Log file: D:\result\schedule_log.txt
- Test messages ensure system functionality
- OpenClaw integration ensures 100% delivery guarantee