* ENHANCEMENT
  * make `ttl` mandatory for add function
  * add `requests` to requirements
* BUGFIX
  * update (delete + create) records with different `ttl` to prevent duplicate entries
  * add a workaround to prevent CNAME creation if a record with the same name already exists
