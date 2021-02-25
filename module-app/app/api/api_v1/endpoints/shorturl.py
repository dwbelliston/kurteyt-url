"""ShortUrl API"""


from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app import crud, exceptions, models
from app.api import deps
from app.core.logger import get_logger
from app.core.responses import common_400_and_500

router = APIRouter()

LOGGER = get_logger(__name__)


@router.post(
    "/",
    response_model=models.ShortUrl,
    responses=common_400_and_500,
)
def create_shorturl(
    *,
    shorturl_in: models.ShortUrlCreate,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create shorturl record"""
    LOGGER.debug("Function: create_shorturl")

    try:

        shorturl = crud.shorturl.create_shorturl(obj_in_create=shorturl_in)

        return shorturl

    except (exceptions.ConvertToJsonFailed, exceptions.CreateRecordFailed) as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.message
        )
    except Exception as err:
        LOGGER.exception(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get(
    "/{id}",
    response_model=models.ShortUrl,
    responses=common_400_and_500,
)
def read_shorturl(
    *,
    short_url: str = Path(..., alias="id"),
) -> Any:
    """Get shorturl record"""
    LOGGER.debug(
        (
            f"Function: read_shorturl |",
            f"short_url: {short_url}",
        )
    )

    # Get shorturl
    shorturl_in_db = _get_shorturl(short_url=short_url)

    return shorturl_in_db


@router.delete(
    "/{id}",
    response_model=models.ShortUrl,
    responses=common_400_and_500,
)
def delete_shorturl(
    *,
    short_url: str = Path(..., alias="id"),
) -> Any:
    """Delete shorturl record"""

    LOGGER.debug(
        (
            f"Function: delete_shorturl |",
            f"short_url: {short_url}",
        )
    )

    # Get shorturl
    shorturl_in_db = _get_shorturl(short_url=short_url)

    # Delete the shorturl
    try:
        shorturl = crud.shorturl.delete(db_obj=shorturl_in_db)

    except (exceptions.DeleteRecordFailed) as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.message
        )
    except Exception as err:
        LOGGER.exception(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return shorturl


def _get_shorturl(short_url: str) -> models.ShortUrlInDB:
    """Get shorturl"""

    try:

        shorturl_in_db = crud.shorturl.get_shorturl(shorturl_in=short_url)

        return shorturl_in_db

    except (exceptions.RecordNotFound,) as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message)
    except (exceptions.GetRecordFailed,) as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.message
        )

    except Exception as err:
        LOGGER.exception(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
