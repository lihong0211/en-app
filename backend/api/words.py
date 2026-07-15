# words.py
from fastapi import APIRouter, Query, Depends, status
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from model.words import WordModel, WordBase
from model.word_meanings import WordMeaningsModel
from db import get_db
from core.api_result import success, error, ApiResponse
from utils.dictionary import lookup_word

router = APIRouter(
    prefix="/words", tags=["words"], responses={404: {"description": "Not found"}}
)


class MeaningItem(BaseModel):
    type: str
    content: str


class WordCreate(WordBase):
    meaning: List[MeaningItem] = []


@router.get("/list", response_model=ApiResponse[List[WordBase]], summary="获取word列表")
async def get_words(
    db: Session = Depends(get_db),
    page: int = Query(1, description="页码，从1开始"),  # 修正：从1开始
    page_size: int = Query(10, description="每页记录数", le=10000),
):
    try:
        words = WordModel.select_by(db)
        # 添加分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_words = words[start:end]

        # 为每个单词获取释义
        for word in paginated_words:
            meanings = WordMeaningsModel.select_by(db, {"word_id": word.id})
            word.meaning = [{"type": m.type, "content": m.content} for m in meanings]

        return success(paginated_words)
    except Exception as e:
        return error(f"获取单词列表失败: {str(e)}")


@router.get(
    "/{word_id}", response_model=ApiResponse[WordBase], summary="根据ID获取word"
)
async def get_word(word_id: int, db: Session = Depends(get_db)):
    try:
        word = WordModel.get_by_id(db, word_id)
        if not word:
            return error("单词不存在")

        # 获取单词的释义
        meanings = WordMeaningsModel.select_by(db, {"word_id": word_id})
        # 将释义添加到返回结果中
        result = {
            "id": word.id,
            "word": word.word,
            "en_pronunciation": word.en_pronunciation,
            "us_pronunciation": word.us_pronunciation,
            "created_at": word.created_at,
            "updated_at": word.updated_at,
            "meaning": [{"type": m.type, "content": m.content} for m in meanings],
        }

        return success(result)
    except Exception as e:
        return error(f"获取单词失败: {str(e)}")


@router.post("/add", response_model=ApiResponse[WordBase], summary="创建word")
async def create_word(word: WordCreate, db: Session = Depends(get_db)):
    try:
        existing_word = WordModel.select_one_by(db, {"word": word.word})
        print("existing_word", existing_word)

        if existing_word:
            # 添加详细调试信息
            print(f"找到已存在单词:")
            print(f"  ID: {existing_word.id}")
            print(f"  单词: '{existing_word.word}'")
            print(f"  英文发音: '{existing_word.en_pronunciation}'")
            print(f"  美式发音: '{existing_word.us_pronunciation}'")
            print(f"  删除时间: {existing_word.deleted_at}")
            return error("单词已存在")
        else:
            print("未找到重复单词，可以创建")

        # 创建单词 - 不自动提交，等待释义插入完成后一起提交
        word_data = word.dict(exclude={"meaning"})
        word_id = WordModel.insert(db, word_data, commit=False)  # 不立即提交

        # 创建单词释义
        if word.meaning:
            for meaning_item in word.meaning:
                meaning_data = {
                    "word_id": word_id,
                    "type": meaning_item.type,
                    "content": meaning_item.content,
                }
                WordMeaningsModel.insert(db, meaning_data, commit=False)  # 不立即提交

        # 提交事务
        db.commit()

        # 获取完整的单词信息
        result_word = WordModel.get_by_id(db, word_id)
        meanings = WordMeaningsModel.select_by(db, {"word_id": word_id})
        result = {
            "id": result_word.id,
            "word": result_word.word,
            "en_pronunciation": result_word.en_pronunciation,
            "us_pronunciation": result_word.us_pronunciation,
            "meaning": [{"type": m.type, "content": m.content} for m in meanings],
        }

        return success(result)

    except SQLAlchemyError as e:
        db.rollback()
        return error(f"创建单词失败: {str(e)}")
    except Exception as e:
        db.rollback()
        return error(f"创建单词失败: {str(e)}")


class WordLookupRequest(BaseModel):
    word: str


class WordLookupResponse(WordBase):
    saved: bool = False


@router.post(
    "/lookup", response_model=ApiResponse[WordLookupResponse], summary="查词（有道词典），不自动存库"
)
async def lookup_word_api(payload: WordLookupRequest, db: Session = Depends(get_db)):
    try:
        result = lookup_word(payload.word)
    except RuntimeError as e:
        return error(str(e))
    except Exception as e:
        return error(f"调用有道翻译API失败: {str(e)}")

    if not result:
        return error("查询不到这个单词")

    existing = WordModel.select_one_by(db, {"word": result["word"]})
    result["saved"] = existing is not None

    return success(result)


@router.post("/update", response_model=ApiResponse[WordBase], summary="更新word")
async def update_word(
    word_id: int = Query(..., description="wordID"),
    word_data: WordCreate = None,
    db: Session = Depends(get_db),
):
    try:
        existing_word = WordModel.get_by_id(db, word_id)
        if not existing_word:
            return error("单词不存在")

        update_dict = word_data.dict(exclude_unset=True, exclude={"meaning"})

        if "word" in update_dict and update_dict["word"] != existing_word.word:
            word_exists = WordModel.select_one_by(db, {"word": update_dict["word"]})
            if word_exists and word_exists.id != word_id:
                return error("单词已存在")

        # 更新单词基本信息 - 不自动提交
        update_dict["id"] = word_id
        WordModel.update(db, update_dict, commit=False)

        # 处理单词释义
        if hasattr(word_data, "meaning") and word_data.meaning is not None:
            # 先删除原有的释义
            WordMeaningsModel.delete_by(db, {"word_id": word_id}, commit=False)

            # 插入新的释义
            for meaning_item in word_data.meaning:
                meaning_data = {
                    "word_id": word_id,
                    "type": meaning_item.type,
                    "content": meaning_item.content,
                }
                WordMeaningsModel.insert(db, meaning_data, commit=False)

        # 提交事务
        db.commit()

        # 获取更新后的完整单词信息
        result_word = WordModel.get_by_id(db, word_id)
        meanings = WordMeaningsModel.select_by(db, {"word_id": word_id})
        result = {
            "id": result_word.id,
            "word": result_word.word,
            "en_pronunciation": result_word.en_pronunciation,
            "us_pronunciation": result_word.us_pronunciation,
            "created_at": result_word.created_at,
            "updated_at": result_word.updated_at,
            "meaning": [{"type": m.type, "content": m.content} for m in meanings],
        }

        return success(result)

    except SQLAlchemyError as e:
        db.rollback()
        return error(f"更新单词失败: {str(e)}")
    except Exception as e:
        db.rollback()
        return error(f"更新单词失败: {str(e)}")


@router.post("/delete", status_code=status.HTTP_200_OK, summary="删除word")
async def delete_word(
    word_id: int = Query(..., description="wordID"), db: Session = Depends(get_db)
):
    try:
        WordModel.delete(db, word_id)
        return success()
    except Exception as e:
        return error(f"删除单词失败: {str(e)}")
