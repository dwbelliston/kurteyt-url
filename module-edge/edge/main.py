"""
Lambda@edge

If not an api route, check url slug and redirect based on record in dynamodb
"""

import boto3
from edge import logger

LOGGER = logger.get_logger(__name__)

# Setup boto3
SESSION = boto3.session.Session()
AWS_REGION = "us-east-1"

# Dyanmodb table name
KERTEYT_TABLE_NAME = None
EXPIRED_REDIRECT = None

# Lazy init cli
RES_CONTACT_TABLE = None

# Setup logger
LOGGER = logger.get_logger("index")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <!-- OG settings -->
    <meta property="og:title" content="$OG_TITLE" />
    <meta property="og:description" content="$OG_DESCRIPTION" />
    <meta property="og:url" content="$OG_URL" />
    <meta property="og:image" content="$OG_IMAGE" />
    <meta property="og:image:alt" content="$OG_IMAGE_ALT" />
    <meta property="og:type" content="website" />
    <title>CurrentClient</title>
    <link
      rel="stylesheet"
      href="node_modules/modern-normalize/modern-normalize.css"
    />

    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"
      rel="stylesheet"
    />

    <link
      href="https://fonts.googleapis.com/css2?family=Caveat&display=swap"
      rel="stylesheet"
    />

    <script>
      window.onload = function () {
        // similar behavior as clicking on a link
        setTimeout(() => {
          // window.location.href = "$REDIRECT_URL";
          window.location = "$REDIRECT_URL";
        }, 3000);
      };
    </script>
    <style>
      html {
        font-size: 16px;
      }

      body {
        margin: 0px;
        font-family: "Inter", sans-serif;
      }

      .gotobutton {
        text-align: center;
        display: block;
        text-decoration: none;
        background-color: white;
        color: #6b7280;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.75rem;
      }
      .gotobutton:hover {
        background-color: #f4f4f5;
      }

      .gotobutton:active {
        background-color: #d1d5db;
      }

      .gotobutton:visited {
        background-color: #ccc;
      }

      .signature {
        text-align: right;
        font-size: 24px;
        font-family: "Caveat", cursive;
      }

      .spinner-2 {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: radial-gradient(farthest-side, #3b82f6 94%, #0000) top/8px
            8px no-repeat,
          conic-gradient(#0000 30%, #3b82f6);
        -webkit-mask: radial-gradient(
          farthest-side,
          #0000 calc(100% - 8px),
          #000 0
        );
        animation: s3 1s infinite linear;
      }

      @keyframes s3 {
        100% {
          transform: rotate(1turn);
        }
      }

      .aspect-ratio-box {
        width: 100%;
        position: relative;
      }

      .aspect-ratio-box::after {
        display: block;
        content: "";
        padding-bottom: 52.6%;
      }

      .aspect-ratio-box img {
        position: absolute;
        left: 0;
        object-fit: cover;
        top: 0;
        width: 100%;
        height: 100%;
      }

      .container {
        padding-left: 1.5rem;
        padding-right: 1.5rem;
      }

      .card {
        position: relative;
        overflow: hidden;
        background: white;
        border-width: 1px;
        border-radius: 8px;
        border-style: solid;
        border-color: #e5e7eb;
      }

      .card + .card {
        margin-top: 2rem;
      }
    </style>
  </head>
  <body>
    <div style="min-height: 100vh">
      <!-- colored header -->
      <div
        style="
          background-color: #eff6ff;
          height: 36vh;
          border-bottom-width: 1px;
          border-style: solid;
          border-color: #e5e7eb;
        "
      ></div>

      <!-- upmargined form -->
      <div
        style="
          display: flex;
          flex-direction: column;
          align-items: center;
          padding-left: 2rem;
          padding-right: 2rem;
        "
      >
        <div style="width: 100%; max-width: 32rem; margin-top: -32vh">
          <!-- Text header -->
          <div
            style="
              font-size: 1rem;
              padding-top: 0.5rem;
              text-align: left;
              margin-bottom: 2rem;
            "
          >
            <p style="font-size: 1rem; font-weight: 700; margin: 0">
              $OG_TITLE
            </p>
            <p
              style="
                font-size: 0.8rem;
                font-weight: 400;
                margin: 0;
                color: #6b7280;
                padding-top: 0.5rem;
              "
            >
              $OG_DESCRIPTION
            </p>
          </div>

          <!-- Image header -->
          <div class="card">
            <div class="aspect-ratio-box">
              <img src="$OG_IMAGE" alt="$OG_IMAGE_ALT" />
            </div>
          </div>

          <!-- Loading -->

          <div class="card">
            <div
              class="container"
              style="padding-top: 1rem; padding-bottom: 2rem"
            >
              <p style="font-size: 1rem; text-align: center">
                Preparing your information...
              </p>
              <div style="margin-top: 2rem">
                <div style="margin: auto" class="spinner-2"></div>
              </div>
            </div>
          </div>

          <!-- Redirect -->

          <div class="card">
            <div
              class="container"
              style="padding-top: 1rem; padding-bottom: 1rem"
            >
              <a href="$REDIRECT_URL" class="gotobutton"
                >Click here if you are not redirected
                <span>&#10230;</span>
              </a>
            </div>
          </div>
        </div>

        <div>
          <p
            style="
              font-size: smaller;
              margin-top: 2rem;
              margin-bottom: 1rem;
              color: #6b7280;
            "
          >
            Running on
            <strong
              ><a
                style="text-decoration: none; color: #6b7280 !important"
                href="https://currentclient.com"
                >CurrentClient</a
              ></strong
            >
          </p>
        </div>
      </div>
    </div>
  </body>
</html>


"""


SUPPORTED_STATUS_CODES = {
    "200": "OK",
    "301": "Moved Permanently",
    "302": "Found",
    "307": "Temporary Redirect",
}


# Check its not an api route
def check_is_apiroute(path):
    """Check its an api route or a redirectable slug"""
    LOGGER.info(f"Checking is api route: {path}")
    is_apiroute = False

    if path.startswith("docs"):
        is_apiroute = True
    if path.startswith("api/"):
        is_apiroute = True
    if path.startswith("openapi"):
        is_apiroute = True

    return is_apiroute


def check_is_getmethod(method):
    """Check its a redirectable method"""
    LOGGER.info(f"Checking is get method: {method}")
    is_method = False

    if method == "GET":
        is_method = True

    return is_method


def get_redirect_record(slug):
    """Get redirect record from dynamodb"""

    LOGGER.info(f"Getting dynamod record with pk: {slug}")

    redirect_record = {}

    cleaned_slug = run_format_short_id(slug)

    try:

        global RES_CONTACT_TABLE  # pylint: disable=global-statement

        if not RES_CONTACT_TABLE:
            RES_CONTACT_TABLE = SESSION.resource(
                service_name="dynamodb", region_name=AWS_REGION
            ).Table(KERTEYT_TABLE_NAME)

        get_response = RES_CONTACT_TABLE.get_item(
            Key={
                # PK and SK are on the record being passed in for updates
                "PK": cleaned_slug,
            },
            ConsistentRead=False,  # True|False,
        )

        redirect_record = get_response.get("Item", False)

    except Exception as err:
        LOGGER.exception(err)

    return redirect_record


# Return redirect
def build_og_redirect(response, redirect_record):
    """Build the og redirect response"""

    og_settings = redirect_record.get("OgSettings", {})
    target_url = redirect_record.get("TargetUrl", {})

    # pull og values
    og_title = og_settings.get("OgTitle", "")
    og_description = og_settings.get("OgDescription", "")
    og_url = og_settings.get("OgUrl", "")
    og_image = og_settings.get("OgImage", "")
    og_image_alt = og_settings.get("OgImage_alt", "")

    html_page = (
        HTML_TEMPLATE.replace("$OG_TITLE", og_title)
        .replace("$OG_DESCRIPTION", og_description)
        .replace("$OG_URL", og_url)
        .replace("$OG_IMAGE", og_image)
        .replace("$OG_IMAGE_ALT", og_image_alt)
        .replace("$REDIRECT_URL", target_url)
    )

    response = {
        "status": "200",
        "statusDescription": "OK",
        "headers": {
            "cache-control": [{"key": "Cache-Control", "value": "max-age=100"}],
            "content-type": [{"key": "Content-Type", "value": "text/html"}],
        },
        "body": html_page,
    }

    return response


# Return redirect
def build_direct_redirect(response, redirect_record, status_code="301"):
    """Build the direct redirect response"""

    redirect_to_url = redirect_record.get("TargetUrl")
    LOGGER.info(f"Direct redirect to: {redirect_to_url}")

    response = {
        "status": status_code,
        "statusDescription": SUPPORTED_STATUS_CODES[status_code],
        "headers": {
            "cache-control": [{"key": "Cache-Control", "value": "max-age=100"}],
            "content-type": [{"key": "Content-Type", "value": "text/html"}],
            "location": [{"key": "Location", "value": redirect_to_url}],
        },
    }

    return response


def make_response(cloudfront_event):
    """Check the request and determine response"""

    request = cloudfront_event["request"]

    # request.uri is just the URL path without hostname or querystring
    requested_path = request["uri"]
    # Remove leading and ending slash
    requested_slug = requested_path.lstrip("/").rstrip("/")

    requested_method = request["method"]

    # Return original and let it continue
    if check_is_apiroute(requested_slug):
        LOGGER.info("Forward to API")
        return request

    # If its not a GET method, dont redirect
    if not check_is_getmethod(requested_method):
        LOGGER.info("Forward to API, not a GET")
        return request

    # Read slug from dynamodb to get redirect path
    redirect_record = get_redirect_record(requested_slug)

    if not redirect_record:
        LOGGER.info("Forward to API, no redirect recorded")
        redirect_record = {"TargetUrl": EXPIRED_REDIRECT}

    # Find target URL
    redirect_type = redirect_record.get("RedirectType")

    response = {
        "headers": request["headers"],
        "status": "200",
        "statusDescription": "OK",
    }

    # OG html type
    if redirect_type == "OG_HTML":
        response = build_og_redirect(response, redirect_record)

    # Direct type
    else:
        response = build_direct_redirect(response, redirect_record)

    return response


def run_format_short_id(short_id_in: str):
    """
    Convert the short id if it has u/ to be lowercase
    """

    cleaned_short_id = short_id_in

    if short_id_in.lower().startswith("u/"):
        cleaned_short_id = "u/" + short_id_in[2:].lower()

    return cleaned_short_id


def handler(evt=None, ctx=None):
    """Handle viewer-request"""

    LOGGER.info(f"FULL EVENT: {evt}")

    try:
        #  Get the incoming request and the initial response from S3
        #  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html
        cloudfront_event = evt["Records"][0]["cf"]

        res = make_response(cloudfront_event)

        return res

    except Exception as err:
        LOGGER.error("Failed with error: %s", err)
        raise err


# Different handler for each env to handle
# to set env variables, since cant pass in
# env variables to lambda @edge function


def handler_dev(evt=None, ctx=None):
    """dev env"""
    global KERTEYT_TABLE_NAME
    global EXPIRED_REDIRECT
    KERTEYT_TABLE_NAME = "cc-east-dev-db-kurteyt"
    EXPIRED_REDIRECT = "https://client.currentclient.io/expired"
    return handler(evt, ctx)


def handler_prd(evt=None, ctx=None):
    """prd env"""
    global KERTEYT_TABLE_NAME
    global EXPIRED_REDIRECT
    KERTEYT_TABLE_NAME = "cc-east-prd-db-kurteyt"
    EXPIRED_REDIRECT = "https://client.currentclient.com/expired"
    return handler(evt, ctx)
