tell application "Skype"
  activate
  delay 2
  set status to send command "CALL %s" script name "Call ME"
  activate
end tell