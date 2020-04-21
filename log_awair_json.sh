(echo -n "$(date +%s) "; curl -s http://192.168.88.235/air-data/latest; echo "") | tee -a awair.log
