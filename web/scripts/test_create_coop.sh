#!/bin/bash

read -d '' req << EOF
{
  "name": "Test Dave 9999",
  "types": [
      {"name": "Library"}
  ],
  "coop_address_tags": [
    {
      "is_public": true,
      "address": 
      {
        "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
        "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
        "locality": {
          "name": "Chicago",
          "postal_code": "60654",
          "state": {
            "id": "19313", 
            "name": "Illinois",
            "code": "IL",
            "country": {
              "name": "United States" 
            }
          }
        }
      }
    }
  ],
  "enabled": "true",
  "contact_methods": [
    {
      "type": "EMAIL",
      "is_public": true,
      "email": "myemail@example.com"
    },
    {
      "type": "PHONE",
      "is_public": true,
      "phone": "+17739441426"
    }          
  ],
  "description": "My Coop Description",
  "web_site": "http://www.1871.com/"
}
EOF

echo $req
echo "<br><br>"

curl --user admin:admin --header "Content-type: application/json" --data "$req" --request POST "http://localhost:8000/coops/"  
 
