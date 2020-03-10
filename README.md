# Stater

the server-side of the Stater-System

## API-Overview

all endpoints are POST.

required; _optional_

| endpoint             | description                                               | parameters                                                                                        |
| -------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| /api/getserver       | Return information about certain server                   | name                                                                                              |
| /api/registerserver  | Register a new server                                     | name, password, _description_, _repoURL_, _mainStatus_, _components_                              |
| /api/changeserver    | Change an existing server                                 | id/name, password, _newName_, _description_, _repoURL_, _mainStatus_, _components_, _newPassword_ |
| /api/updateserver    | Update server status. Can also be used to set components. | name, password, _mainStatus_, _components_                                                        |
| /api/deleteserver    | Delete a server completely from the system. No return!    | name/id, password                                                                                 |
| /api/updatecomponent | Update the status of a certain component                  | name, password, component, status                                                                 |
