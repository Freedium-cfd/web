from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class MediumPostContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    bodyModel: dict[str, Any] | None = None
    isFullContent: bool | None = None
    isLockedPreviewOnly: bool | None = None
    metaDescription: str | None = None
    postDisplay: dict[str, Any] | None = None
    subtitle: str | None = None


class MediumPostVirtuals(BaseModel):
    model_config = ConfigDict(extra="allow")

    allowNotes: bool | None = None
    imageCount: int | None = None
    isBookmarked: bool | None = None
    isLockedPreviewOnly: bool | None = None
    links: dict[str, Any] | None = None
    metaDescription: str | None = None
    noIndex: bool | None = None
    previewImage: dict[str, Any] | None = None
    publishedInCount: int | None = None
    readingList: int | None = None
    readingTime: float | None = None
    recommends: int | None = None
    responsesCreatedCount: int | None = None
    sectionCount: int | None = None
    socialRecommendsCount: int | None = None
    statusForCollection: str | None = None
    subtitle: str | None = None
    tags: list[Any] | None = None
    topics: list[Any] | None = None
    totalClapCount: int | None = None
    usersBySocialRecommends: list[Any] | None = None
    wordCount: int | None = None


class MediumPostValue(BaseModel):
    model_config = ConfigDict(extra="allow")

    acceptedAt: int | None = None
    allowResponses: bool | None = None
    approvedHomeCollectionId: str | None = None
    audioVersionDurationSec: int | None = None
    canonicalUrl: str | None = None
    cardType: int | None = None
    content: MediumPostContent | None = None
    coverless: bool | None = None
    createdAt: int | None = None
    creatorId: str | None = None
    curationEligibleAt: int | None = None
    deletedAt: int | None = None
    detectedLanguage: str | None = None
    displayAuthor: str | None = None
    editorialPreviewDek: str | None = None
    editorialPreviewTitle: str | None = None
    experimentalCss: str | None = None
    featureLockRequestAcceptedAt: int | None = None
    firstPublishedAt: int | None = None
    hasUnpublishedEdits: bool | None = None
    hightowerMinimumGuaranteeEndsAt: int | None = None
    hightowerMinimumGuaranteeStartsAt: int | None = None
    homeCollectionId: str | None = None
    id: str | None = None
    importedPublishedAt: int | None = None
    importedUrl: str | None = None
    inResponseToMediaResourceId: str | None = None
    inResponseToPostId: str | None = None
    inResponseToRemovedAt: int | None = None
    isApprovedTranslation: bool | None = None
    isBlockedFromHightower: bool | None = None
    isDistributionAlertDismissed: bool | None = None
    isEligibleForRevenue: bool | None = None
    isLimitedState: bool | None = None
    isLockedResponse: bool | None = None
    isMarkedPaywallOnly: bool | None = None
    isNewsletter: bool | None = None
    isProxyPost: bool | None = None
    isPublishToEmail: bool | None = None
    isSeries: bool | None = None
    isShortform: bool | None = None
    isSubscriptionLocked: bool | None = None
    isSuspended: bool | None = None
    isTitleSynthesized: bool | None = None
    latestPublishedAt: int | None = None
    latestPublishedVersion: str | None = None
    latestRev: int | None = None
    latestVersion: str | None = None
    layerCake: int | None = None
    license: int | None = None
    lockedPostSource: int | None = None
    mediumUrl: str | None = None
    migrationId: str | None = None
    mongerRequestType: int | None = None
    newsletterId: str | None = None
    notifyFacebook: bool | None = None
    notifyFollowers: bool | None = None
    notifyTwitter: bool | None = None
    previewContent: MediumPostContent | None = None
    previewContent2: MediumPostContent | None = None
    primaryTopic: dict[str, Any] | None = None
    primaryTopicId: str | None = None
    proxyPostFaviconUrl: str | None = None
    proxyPostProviderName: str | None = None
    proxyPostType: int | None = None
    responseDistribution: int | None = None
    responseHiddenOnParentPostAt: int | None = None
    responsesLocked: bool | None = None
    seoTitle: str | None = None
    sequenceId: str | None = None
    seriesLastAppendedAt: int | None = None
    shortformType: int | None = None
    slug: str | None = None
    socialDek: str | None = None
    socialTitle: str | None = None
    title: str | None = None
    translationSourceCreatorId: str | None = None
    translationSourcePostId: str | None = None
    type: str | None = None
    uniqueSlug: str | None = None
    updatedAt: int | None = None
    versionId: str | None = None
    virtuals: MediumPostVirtuals | None = None
    visibility: int | None = None
    vote: bool | None = None
    webCanonicalUrl: str | None = None


class MediumCollectionReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    ampLogo: dict[str, Any] | None = None
    collectionFeatures: list[Any] | None = None
    collectionMastheadId: str | None = None
    colorBehavior: int | None = None
    colorPalette: dict[str, Any] | None = None
    creatorId: str | None = None
    description: str | None = None
    domain: str | None = None
    facebookPageName: str | None = None
    favicon: dict[str, Any] | None = None
    googleAnalyticsId: str | None = None
    header: dict[str, Any] | None = None
    id: str | None = None
    image: dict[str, Any] | None = None
    instagramUsername: str | None = None
    isCurationAllowedByDefault: bool | None = None
    isOptedIntoAurora: bool | None = None
    lightText: bool | None = None
    logo: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    name: str | None = None
    navItems: list[Any] | None = None
    newsletterV3: dict[str, Any] | None = None
    paidForDomainAt: int | None = None
    polarisCoverImage: dict[str, Any] | None = None
    ptsQualifiedAt: int | None = None
    publicEmail: str | None = None
    sections: list[Any] | None = None
    shortDescription: str | None = None
    slug: str | None = None
    subscriberCount: int | None = None
    tagline: str | None = None
    tags: list[Any] | None = None
    tintColor: str | None = None
    twitterUsername: str | None = None
    type: str | None = None
    virtuals: dict[str, Any] | None = None


class MediumUserReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    allowNotes: int | None = None
    backgroundImageId: str | None = None
    bio: str | None = None
    createdAt: int | None = None
    facebookDisplayName: str | None = None
    firstOpenedAndroidApp: int | None = None
    firstOpenedIosApp: int | None = None
    hasCompletedProfile: bool | None = None
    hasSeenIcelandOnboarding: bool | None = None
    imageId: str | None = None
    isCreatorPartnerProgramEnrolled: bool | None = None
    isMembershipTrialEligible: bool | None = None
    isSuspended: bool | None = None
    isWriterProgramEnrolled: bool | None = None
    languageCode: str | None = None
    mediumMemberAt: int | None = None
    name: str | None = None
    optInToIceland: bool | None = None
    postSubscribeMembershipUpsellShownAt: int | None = None
    social: dict[str, Any] | None = None
    socialStats: dict[str, Any] | None = None
    subdomainCreatedAt: int | None = None
    twitterScreenName: str | None = None
    type: str | None = None
    userDismissableFlags: list[Any] | None = None
    userFlags: list[Any] | None = None
    userId: str | None = None
    username: str | None = None


class MediumSocialReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    targetUserId: str | None = None
    type: str | None = None
    userId: str | None = None


class MediumSocialStatsReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str | None = None
    userId: str | None = None
    usersFollowedByCount: int | None = None
    usersFollowedCount: int | None = None


class MediumPostReferences(BaseModel):
    model_config = ConfigDict(extra="allow")

    Collection: dict[str, MediumCollectionReference] | None = None
    Social: dict[str, MediumSocialReference] | None = None
    SocialStats: dict[str, MediumSocialStatsReference] | None = None
    User: dict[str, MediumUserReference] | None = None


class MediumPostPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    collaborators: list[Any] | None = None
    collectionUserRelations: list[Any] | None = None
    hideMeter: bool | None = None
    mentionedUsers: list[Any] | None = None
    mode: str | None = None
    references: MediumPostReferences | None = None
    value: MediumPostValue | None = None


class MediumPostApiResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    b: str | None = None
    payload: MediumPostPayload | None = None
    success: bool | None = None
    v: int | None = None


class MediumPostDataResponse(MediumPostApiResponse):
    pass


# GraphQL-specific models
class GraphQLImageMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    originalWidth: int | None = None
    originalHeight: int | None = None
    focusPercentX: float | None = None
    focusPercentY: float | None = None
    alt: str | None = None


class GraphQLViewerEdge(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    isUser: bool | None = None
    isFollowing: bool | None = None
    isBlocking: bool | None = None
    isMuting: bool | None = None
    isSubscribed: bool | None = None
    isEditor: bool | None = None
    canEditPosts: bool | None = None
    canEditOwnPosts: bool | None = None
    clapCount: int | None = None


class GraphQLSocialStats(BaseModel):
    model_config = ConfigDict(extra="allow")

    followingCount: int | None = None
    followerCount: int | None = None


class GraphQLNewsletterV3(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    viewerEdge: GraphQLViewerEdge | None = None


class GraphQLCreator(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    imageId: str | None = None
    username: str | None = None
    name: str | None = None
    bio: str | None = None
    tippingLink: str | None = None
    viewerEdge: GraphQLViewerEdge | None = None
    socialStats: GraphQLSocialStats | None = None
    newsletterV3: GraphQLNewsletterV3 | None = None
    isFollowing: bool | None = None
    mediumMemberAt: int | None = None
    twitterScreenName: str | None = None


class GraphQLCollection(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    name: str | None = None
    slug: str | None = None
    shortDescription: str | None = None
    avatar: GraphQLImageMetadata | None = None
    subscriberCount: int | None = None
    viewerEdge: GraphQLViewerEdge | None = None
    newsletterV3: GraphQLNewsletterV3 | None = None


class GraphQLMarkup(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    name: str | None = None
    type: str | None = None
    start: int | None = None
    end: int | None = None
    href: str | None = None
    title: str | None = None
    rel: str | None = None
    anchorType: str | None = None
    userId: str | None = None
    creatorIds: list[str] | None = None


class GraphQLCodeBlockMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    lang: str | None = None
    mode: str | None = None


class GraphQLMediaResource(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    iframeSrc: str | None = None
    thumbnailUrl: str | None = None
    iframeHeight: int | None = None
    iframeWidth: int | None = None
    title: str | None = None


class GraphQLIframe(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    iframeHeight: int | None = None
    iframeWidth: int | None = None
    mediaResource: GraphQLMediaResource | None = None


class GraphQLMixtapeMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    mediaResourceId: str | None = None
    href: str | None = None
    thumbnailImageId: str | None = None
    mediaResource: dict[str, Any] | None = None


class GraphQLParagraph(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    name: str | None = None
    href: str | None = None
    text: str | None = None
    iframe: GraphQLIframe | None = None
    layout: str | None = None
    markups: list[GraphQLMarkup] | None = None
    metadata: GraphQLImageMetadata | None = None
    mixtapeMetadata: GraphQLMixtapeMetadata | None = None
    type: str | None = None
    hasDropCap: bool | None = None
    dropCapImage: GraphQLImageMetadata | None = None
    codeBlockMetadata: GraphQLCodeBlockMetadata | None = None


class GraphQLSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    name: str | None = None
    startIndex: int | None = None
    textLayout: str | None = None
    imageLayout: str | None = None
    videoLayout: str | None = None
    backgroundImage: GraphQLImageMetadata | None = None
    backgroundVideo: dict[str, Any] | None = None


class GraphQLRichText(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    sections: list[GraphQLSection] | None = None
    paragraphs: list[GraphQLParagraph] | None = None


class GraphQLContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    bodyModel: GraphQLRichText | None = None
    validatedShareKey: str | None = None


class GraphQLPreviewContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    subtitle: str | None = None


class GraphQLPreviewImage(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None


class GraphQLPostResponses(BaseModel):
    model_config = ConfigDict(extra="allow")

    count: int | None = None


class GraphQLLinkMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str | None = None
    alts: list[dict[str, str]] | None = None


class GraphQLTag(BaseModel):
    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    normalizedTagSlug: str | None = None
    displayTitle: str | None = None
    followerCount: int | None = None
    postCount: int | None = None


class GraphQLPost(BaseModel):
    """Model for GraphQL post response from Medium API."""

    model_config = ConfigDict(extra="allow")

    __typename: str | None = None
    id: str | None = None
    title: str | None = None
    detectedLanguage: str | None = None
    mediumUrl: str | None = None
    latestPublishedVersion: str | None = None
    firstPublishedAt: int | None = None
    updatedAt: int | None = None
    latestPublishedAt: int | None = None
    allowResponses: bool | None = None
    isLocked: bool | None = None
    isProxyPost: bool | None = None
    isSeries: bool | None = None
    canonicalUrl: str | None = None
    visibility: str | None = None
    readingTime: float | None = None
    clapCount: int | None = None
    pinnedByCreatorAt: int | None = None
    responsesLocked: bool | None = None
    inResponseToPostResult: dict[str, Any] | None = None
    inResponseToMediaResource: dict[str, Any] | None = None
    inResponseToEntityType: str | None = None

    creator: GraphQLCreator | None = None
    collection: GraphQLCollection | None = None
    content: GraphQLContent | None = None
    previewContent: GraphQLPreviewContent | None = None
    previewImage: GraphQLPreviewImage | None = None
    viewerEdge: GraphQLViewerEdge | None = None
    postResponses: GraphQLPostResponses | None = None
    linkMetadataList: list[GraphQLLinkMetadata] | None = None
    highlights: list[Any] | None = None
    tags: list[GraphQLTag] | None = None
