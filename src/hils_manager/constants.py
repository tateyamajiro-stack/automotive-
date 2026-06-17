from enum import Enum


class ProjectStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return _PROJECT_STATUS_LABELS[self]


_PROJECT_STATUS_LABELS = {
    ProjectStatus.PLANNING: "計画中",
    ProjectStatus.ACTIVE: "実行中",
    ProjectStatus.ON_HOLD: "保留",
    ProjectStatus.COMPLETED: "完了",
    ProjectStatus.CANCELLED: "中止",
}


class ProjectRole(Enum):
    DEVELOPMENT_OWNER = "development_owner"
    DEVELOPMENT_LEADER = "development_leader"
    MEMBER_MANAGER = "member_manager"
    PRIMARY_DEVELOPER = "primary_developer"
    CROSS_DEVELOPER = "cross_developer"

    @property
    def label(self) -> str:
        return _PROJECT_ROLE_LABELS[self]


_PROJECT_ROLE_LABELS = {
    ProjectRole.DEVELOPMENT_OWNER: "開発オーナー",
    ProjectRole.DEVELOPMENT_LEADER: "開発リーダー",
    ProjectRole.MEMBER_MANAGER: "マネージャー(OS)",
    ProjectRole.PRIMARY_DEVELOPER: "主担当(OS)",
    ProjectRole.CROSS_DEVELOPER: "クロス者(OS)",
}


class DeliverableStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"

    @property
    def label(self) -> str:
        return _DELIVERABLE_STATUS_LABELS[self]


_DELIVERABLE_STATUS_LABELS = {
    DeliverableStatus.NOT_STARTED: "未着手",
    DeliverableStatus.IN_PROGRESS: "作業中",
    DeliverableStatus.IN_REVIEW: "レビュー中",
    DeliverableStatus.APPROVED: "承認済",
    DeliverableStatus.REJECTED: "差戻し",
}


class ReviewType(Enum):
    PRE_DELIVERY = "pre_delivery"
    OWNER_BRIEFING = "owner_briefing"
    PEER_REVIEW = "peer_review"

    @property
    def label(self) -> str:
        return _REVIEW_TYPE_LABELS[self]


_REVIEW_TYPE_LABELS = {
    ReviewType.PRE_DELIVERY: "納品前レビュー",
    ReviewType.OWNER_BRIEFING: "オーナー説明",
    ReviewType.PEER_REVIEW: "ピアレビュー",
}


class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class RequirementPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def label(self) -> str:
        return _REQUIREMENT_PRIORITY_LABELS[self]


_REQUIREMENT_PRIORITY_LABELS = {
    RequirementPriority.CRITICAL: "最重要",
    RequirementPriority.HIGH: "高",
    RequirementPriority.MEDIUM: "中",
    RequirementPriority.LOW: "低",
}


class RequirementStatus(Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    DEFERRED = "deferred"
    REJECTED = "rejected"

    @property
    def label(self) -> str:
        return _REQUIREMENT_STATUS_LABELS[self]


_REQUIREMENT_STATUS_LABELS = {
    RequirementStatus.NEW: "新規",
    RequirementStatus.ACCEPTED: "受理",
    RequirementStatus.IN_PROGRESS: "対応中",
    RequirementStatus.IMPLEMENTED: "実装済",
    RequirementStatus.VERIFIED: "検証済",
    RequirementStatus.DEFERRED: "延期",
    RequirementStatus.REJECTED: "却下",
}


class WBSStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return _WBS_STATUS_LABELS[self]


_WBS_STATUS_LABELS = {
    WBSStatus.NOT_STARTED: "未着手",
    WBSStatus.IN_PROGRESS: "作業中",
    WBSStatus.COMPLETED: "完了",
    WBSStatus.BLOCKED: "ブロック中",
    WBSStatus.CANCELLED: "中止",
}


class EstimateType(Enum):
    INITIAL = "initial"
    REVISED = "revised"
    FINAL = "final"

    @property
    def label(self) -> str:
        return _ESTIMATE_TYPE_LABELS[self]


_ESTIMATE_TYPE_LABELS = {
    EstimateType.INITIAL: "初回見積",
    EstimateType.REVISED: "修正見積",
    EstimateType.FINAL: "最終見積",
}


class RiskProbability(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskImpact(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskStatus(Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"

    @property
    def label(self) -> str:
        return _RISK_STATUS_LABELS[self]


_RISK_STATUS_LABELS = {
    RiskStatus.OPEN: "未対応",
    RiskStatus.MITIGATING: "対策中",
    RiskStatus.RESOLVED: "解決済",
    RiskStatus.ACCEPTED: "受容",
}


class ProcessPhase(Enum):
    PLANNING = "planning"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    DELIVERY = "delivery"

    @property
    def label(self) -> str:
        return _PROCESS_PHASE_LABELS[self]


_PROCESS_PHASE_LABELS = {
    ProcessPhase.PLANNING: "計画",
    ProcessPhase.DESIGN: "設計",
    ProcessPhase.IMPLEMENTATION: "実装",
    ProcessPhase.TEST: "テスト",
    ProcessPhase.DELIVERY: "納品",
}
