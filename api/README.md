# GuidGrabber API

## POST `/lab/<labconfig>/<code>/guid`

Register a new GUID to a lab config with a given code by sending lab data in JSON format in a POST message body.

The lab config must already exist in the GuidGrabber etc directory and must have a labconfig.csv that includes an `apitoken` column.

The request to the API must include the value of the `apitoken` in an `Authentication: Bearer` header.

Example:

```
curl -XPOST https://www.opentlc.com/gg/api.cgi/lab/user-example.com/test/guid -d '{"guid":"abce","redirect_url":"https://example.com/"}' --header 'Authorization: Bearer s3cr3t-t0k3n'
```
