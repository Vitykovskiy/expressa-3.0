# Integration Contracts

## API Contracts

| Contract | Producer | Consumer | Request | Response / Event | Notes |
| --- | --- | --- | --- | --- | --- |
| `<contract>` | `<producer>` | `<consumer>` | `<shape>` | `<shape>` | `<notes>` |

## Event Contracts

| Event | Producer | Consumer | Payload | Notes |
| --- | --- | --- | --- | --- |
| `<event>` | `<producer>` | `<consumer>` | `<payload>` | `<notes>` |

## External Integrations

| Integration | Purpose | Contract reference | Failure handling |
| --- | --- | --- | --- |
| `<integration>` | `<purpose>` | `<reference>` | `<handling>` |

## Rule

Implementation contours must consume or produce contracts from this file. If a required contract is missing, return to `analysis`.
