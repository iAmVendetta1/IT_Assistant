from fastapi import Request


async def get_current_user(request: Request) -> str:
    # TODO: Validate Azure AD JWT token and return the user's OID claim
    # token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    # claims = await validate_azure_token(token)
    # return claims["oid"]
    return "local_dev_user"
