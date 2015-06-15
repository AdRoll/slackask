import sqlalchemy as sa
from enum import Enum
from sqlalchemy.ext import declarative

# this is incredible thread-safe (because of a sqlalchemy magic)
_scoped_session = None


def create_db_session(database_url=None):
    global _scoped_session
    if database_url is None and _scoped_session is None:
        raise RuntimeError("Database not initialized")
    if _scoped_session is None:
        engine = sa.create_engine(database_url, convert_unicode=True)
        session = sa.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _scoped_session = sa.orm.scoped_session(session)
        Base.metadata.create_all(engine)
    return _scoped_session

Base = declarative.declarative_base()

class QuestionStatus(Enum):
    pending=1
    published=2
    deleted=3
    all=4
    @staticmethod
    def statusForName(nameString):
        if nameString == "pending":
            return QuestionStatus.pending
        if nameString == "published":
            return QuestionStatus.published
        if nameString == "deleted":
            return QuestionStatus.deleted
        if nameString == "all":
            return QuestionStatus.all
        return QuestionStatus.pending

    @staticmethod
    def nameForStatus(status):
        if status == QuestionStatus.pending:
            return "pending"
        if status == QuestionStatus.published:
            return "published"
        if status == QuestionStatus.deleted:
            return "deleted"
        if status == QuestionStatus.all:
            return "all"
        # this is the default status if somebody gives us one we don't recognize


class Question(Base):
    __tablename__ = 'questions'
    number = sa.Column(
        sa.Integer,
        nullable=False,
        primary_key=True
    )
    status = sa.Column(
        sa.Integer,
        nullable=False,
        default=1
    )
    username = sa.Column(
        sa.UnicodeText,
        nullable=False,
        primary_key=True
    )

    question = sa.Column(
        sa.UnicodeText,
        nullable=False
    )

class UserIndex(Base):
    __tablename__ = 'user_index'
    number = sa.Column(
        sa.Integer,
        nullable=False,
        default=1,
    )

    username = sa.Column(
        sa.UnicodeText,
        nullable=False,
        primary_key=True
    )
