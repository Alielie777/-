from typing import Optional
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="更新时间"
    )

class Category(BaseModel):
    __tablename__ = "news_category"

    id : Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分类id"
    )
    name : Mapped[str] = mapped_column(
        String(50),
        unique=True,       # 名称唯一
        nullable=False,    # 不允许为空
        comment="分类名称"
    )
    sort_order : Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序 "
    )

    def __repr__(self):
        return f"<Category id={self.id!r}, name={self.name!r}, sort_order={self.sort_order!r}>"


class News(BaseModel):
    __tablename__ = "news"
    # 为常用筛选和排序字段建立索引，提升查询效率
    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),
        Index("idx_publish_time", "publish_time"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="新闻ID",
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="新闻标题"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="新闻简介"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="新闻内容"
    )
    image: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="封面图片URL"
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="作者"
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news_category.id"),
        nullable=False,
        comment="分类ID",
    )
    views: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="浏览量"
    )
    publish_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="发布时间"
    )

    def __repr__(self):
        return (
            f"<News id={self.id!r}, title={self.title!r}, "
            f"views={self.views!r}>"
        )
