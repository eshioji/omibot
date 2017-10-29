tell application "Skype"
  set status to send command "CALL %s" script name "Call ME"
  activate
end tell