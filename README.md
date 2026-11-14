|         |    |    |         |
| ------- | -- | -- | ------  |
| Biller  | 1  | 1+ | Bill    |
| Bill    | 1+ | 1  | Account |
| Account | 1  | 1+ | Meter   |
| Meter   | 1  | 1+ | Reading |

- A biller can have one or more bills.
- One or more bills can have a single account.
- An account can contain one or more meters.
- A meter can have multiple meter readings.