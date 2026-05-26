from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Match, Player, Round, User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_username(request: Request):
    return request.cookies.get("user")


def current_user(request: Request, db: Session):
    username = current_username(request)

    if not username:
        return None

    return db.query(User).filter(User.username == username).first()


def login_redirect():
    return RedirectResponse("/login", status_code=302)


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    if not current_username(request):
        return login_redirect()

    matches = db.query(Match).order_by(Match.created_at.desc()).all()
    active_count = len([match for match in matches if not match.is_finished])
    finished_count = len([match for match in matches if match.is_finished])

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "matches": matches,
            "active_count": active_count,
            "finished_count": finished_count,
            "current_user": current_username(request)
        }
    )


@router.get("/history")
def history(
    request: Request,
    db: Session = Depends(get_db)
):
    if not current_username(request):
        return login_redirect()

    matches = db.query(Match).order_by(Match.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "request": request,
            "matches": matches,
            "current_user": current_username(request)
        }
    )


@router.get("/profile")
def profile(
    request: Request,
    db: Session = Depends(get_db)
):
    if not current_username(request):
        return login_redirect()

    user = current_user(request, db)
    matches = db.query(Match).order_by(Match.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "request": request,
            "user": user,
            "matches": matches,
            "active_count": len([match for match in matches if not match.is_finished]),
            "finished_count": len([match for match in matches if match.is_finished]),
            "current_user": current_username(request)
        }
    )


@router.get("/create-match")
def create_match_page(request: Request):
    if not current_username(request):
        return login_redirect()

    return templates.TemplateResponse(
        request,
        "create_match.html",
        {
            "request": request,
            "current_user": current_username(request)
        }
    )


@router.post("/create-match")
def create_match(
    request: Request,
    name: str = Form(...),
    target_score: int = Form(...),
    players: str = Form(...),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return login_redirect()

    match = Match(
        name=name,
        target_score=target_score,
        created_by=user.id if user else 1
    )

    db.add(match)
    db.commit()
    db.refresh(match)

    player_names = players.split(",")

    for p in player_names:
        player = Player(
            name=p.strip(),
            match_id=match.id
        )

        db.add(player)

    db.commit()

    return RedirectResponse(
        f"/match/{match.id}",
        status_code=302
    )


@router.get("/match/{match_id}")
def match_page(
    match_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not current_username(request):
        return login_redirect()

    match = db.query(Match).filter(Match.id == match_id).first()

    players = db.query(Player).filter(
        Player.match_id == match_id
    ).all()

    return templates.TemplateResponse(
        request,
        "match.html",
        {
            "request": request,
            "match": match,
            "players": players,
            "current_user": current_username(request)
        }
    )


@router.post("/match/{match_id}/round")
async def add_round(
    match_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not current_username(request):
        return login_redirect()

    form = await request.form()

    players = db.query(Player).filter(
        Player.match_id == match_id
    ).all()

    winner = form.get("winner")
    loser_penalty = form.get("loser_penalty")

    round_count = db.query(Round).filter(
        Round.match_id == match_id
    ).count()

    new_round = Round(
        round_number=round_count + 1,
        match_id=match_id
    )

    db.add(new_round)

    for player in players:
        score_value = form.get(f"score_{player.id}") or 0
        score = int(score_value)

        if player.name == winner:
            score = 0

        if player.name == loser_penalty:
            score += 50

        player.total_score += score

    match = db.query(Match).filter(
        Match.id == match_id
    ).first()

    for player in players:
        if player.total_score >= match.target_score:
            match.is_finished = True
            match.loser = player.name

    db.commit()

    return RedirectResponse(
        f"/match/{match_id}",
        status_code=302
    )
