Using kiln, create a composite resource kind called `StaticWebsite`.

Consumers set these things:

- `domainName` (string, required): the custom domain the site is served on, for example `www.example.com`.
- `hostedZoneId` (string, required): the ID of the existing public Route 53 hosted zone that serves that domain.
- `region` (string, defaulting to `ap-southeast-1`): where the S3 bucket lives.

A `StaticWebsite` composes everything needed to serve the site's files over HTTPS on `domainName`:

- A private S3 bucket that holds the site's files. It must not be publicly accessible; only the CDN may read from it.
- An ACM certificate for `domainName`, validated by DNS records in the hosted zone.
- A CDN distribution that serves the bucket on `domainName` with that certificate, sends visitors who use HTTP to HTTPS, and serves `index.html` for the root path.
- A DNS record in the hosted zone that points `domainName` at the CDN.

S3 bucket names are unique across all AWS accounts, so two `StaticWebsite`s must never end
up asking for the same bucket name, even when they have the same `metadata.name` (in
different namespaces, or in different clusters).

Write tests for KCL, and add a sample `StaticWebsite` for `kiln render` to use, with sample observed resources so that
every stage of the composition renders, including the resources that can only exist once AWS has reported on others.
