#!/bin/bash
expect -c '
spawn ./venv/bin/python main.py
expect "✦ ❯ "
send "what model are you?\r"
expect "Answer Completed!"
expect "✦ ❯ "
send "/teach\r"
expect "Action: (A)ccept / (R)eject / Type custom rules to (Augment) > "
send "a\r"
expect "Feedback Learning Session Completed"
expect "✦ ❯ "
send "/quit\r"
expect eof
'
