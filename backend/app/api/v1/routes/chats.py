# app/api/v1/routes/chats.py
from typing import List

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.chat import Chat, ChatParticipant, ChatParticipantRole, ChatType
from app.models.user import User
from app.schemas.chat import ChatRead, DirectChatCreate, DirectChatRead, GroupChatCreate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["chats"])


@router.post("/direct", response_model=DirectChatRead)
async def create_or_get_direct_chat(
    request: DirectChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Chat:
    """
    Создаёт или возвращает существующий direct-чат между двумя пользователями.
    """
    # Проверяем, что other_user существует
    other_user_result = await db.execute(select(User).where(User.id == request.other_user_id))
    other_user = other_user_result.scalar_one_or_none()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    if other_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")

    # Ищем существующий direct-чат между этими двумя пользователями
    # Сначала получаем ID чатов, где есть оба пользователя
    participant_stmt = (
        select(ChatParticipant.chat_id)
        .where(
            and_(
                ChatParticipant.user_id.in_([current_user.id, other_user.id]),
            )
        )
        .group_by(ChatParticipant.chat_id)
        .having(
            func.count(ChatParticipant.user_id) == 2  # Ровно два участника
        )
    )

    chat_ids_result = await db.execute(participant_stmt)
    chat_ids = chat_ids_result.scalars().all()

    # Теперь ищем среди этих чатов direct-чат
    if chat_ids:
        existing_chat_result = await db.execute(
            select(Chat)
            .where(
                and_(
                    Chat.id.in_(chat_ids),
                    Chat.type == ChatType.DIRECT,
                )
            )
            .limit(1)
        )
        chat = existing_chat_result.scalar_one_or_none()

        if chat:
            return chat  # НЕ refresh - просто возвращаем

    # Создаём новый direct-чат
    new_chat = Chat(
        type=ChatType.DIRECT,
        created_by_id=current_user.id,
    )
    db.add(new_chat)
    await db.flush()  # Получаем chat.id

    # Добавляем участников
    participant1 = ChatParticipant(
        chat_id=new_chat.id,
        user_id=current_user.id,
        role=ChatParticipantRole.MEMBER,
    )
    participant2 = ChatParticipant(
        chat_id=new_chat.id,
        user_id=other_user.id,
        role=ChatParticipantRole.MEMBER,
    )

    db.add(participant1)
    db.add(participant2)
    await db.commit()

    # НЕ делаем refresh - participants не нужны в ответе
    return new_chat


@router.post("/group", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_group_chat(
    request: GroupChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Chat:
    """
    Создаёт новый групповой чат.
    """
    # Проверяем, что все participant_ids существуют
    participant_ids = set(request.participant_ids)
    if current_user.id not in participant_ids:
        participant_ids.add(current_user.id)

    users_result = await db.execute(select(User.id).where(User.id.in_(list(participant_ids))))
    existing_user_ids = {row[0] for row in users_result}

    if len(existing_user_ids) != len(participant_ids):
        raise HTTPException(status_code=400, detail="Some users not found")

    if len(participant_ids) < 2:
        raise HTTPException(status_code=400, detail="Group must have at least 2 participants")

    # Создаём чат
    new_chat = Chat(
        title=request.title,
        type=ChatType.GROUP,
        created_by_id=current_user.id,
    )
    db.add(new_chat)
    await db.flush()

    # Добавляем участников (создатель = OWNER)
    for user_id in participant_ids:
        role = (
            ChatParticipantRole.OWNER if user_id == current_user.id else ChatParticipantRole.MEMBER
        )
        participant = ChatParticipant(
            chat_id=new_chat.id,
            user_id=user_id,
            role=role,
        )
        db.add(participant)

    await db.commit()

    # НЕ делаем refresh - participants не нужны
    return new_chat


@router.get("", response_model=List[ChatRead])
async def get_user_chats(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Chat]:
    """
    Возвращает список чатов текущего пользователя.
    """
    stmt = (
        select(Chat)
        .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
        .where(ChatParticipant.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    chats = result.unique().scalars().all()
    return chats
