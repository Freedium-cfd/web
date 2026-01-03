from typing import Any

from freedium_library.services.medium.models import MediumPostDataResponse


def test_medium_post_data_response_parses_payload() -> None:
    sample: dict[str, Any] = {
        "b": "20251219-1743-root",
        "v": 3,
        "success": True,
        "payload": {
            "collaborators": [],
            "collectionUserRelations": [],
            "hideMeter": False,
            "mentionedUsers": [],
            "mode": None,
            "references": {
                "User": {
                    "u1": {
                        "userId": "u1",
                        "username": "alice",
                        "name": "Alice",
                        "createdAt": 1,
                    }
                },
                "Collection": {
                    "c1": {
                        "id": "c1",
                        "name": "Test Collection",
                        "subscriberCount": 5,
                    }
                },
                "Social": {},
                "SocialStats": {},
            },
            "value": {
                "id": "87bda01ea633",
                "title": "Example",
                "content": {
                    "subtitle": "Sub",
                    "isLockedPreviewOnly": False,
                    "bodyModel": {},
                },
                "previewContent": {
                    "subtitle": "Preview",
                    "isFullContent": False,
                    "bodyModel": {},
                },
                "previewContent2": {
                    "subtitle": "Preview2",
                    "isFullContent": False,
                    "bodyModel": {},
                },
                "virtuals": {
                    "readingTime": 3.5,
                    "wordCount": 100,
                    "tags": [],
                    "topics": [],
                    "allowNotes": True,
                },
            },
        },
    }

    model = MediumPostDataResponse.model_validate(sample)

    assert model.success is True
    assert model.payload is not None
    assert model.payload.value is not None
    assert model.payload.value.id == "87bda01ea633"
    assert model.payload.value.virtuals is not None
    assert model.payload.value.virtuals.readingTime == 3.5
    assert model.payload.references is not None
    assert model.payload.references.User is not None
    assert model.payload.references.User["u1"].username == "alice"
