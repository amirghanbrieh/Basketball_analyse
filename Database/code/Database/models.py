
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Club(Base):
    __tablename__ = 'clubs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    league = Column(String(100))
    foundation = Column(String(100))
    to = Column(String(100))
    year = Column(Integer)
    game = Column(Integer)
    win = Column(Integer)
    loss = Column(Integer)
    conf = Column(Integer)
    champ = Column(Integer)


class Season(Base):
    __tablename__ = 'season'
    
    id = Column(Integer, primary_key=True)
    season_years = Column(String(100))


class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    fullname = Column(String(255))
    club_id = Column(Integer, ForeignKey('clubs.id'))
    is_active = Column(Boolean)
    from_year = Column(Integer) 
    to_year = Column(Integer)
    position = Column(String(100))
    shoots = Column(String(50))
    born_year = Column(String(100)) 
    height = Column(Float) 
    weight = Column(Float)
    college_id = Column(Integer, ForeignKey('college.id'))
    highschool_id =Column(Integer, ForeignKey('highschool.id'))
    image_url = Column(String(500))


class Nickname(Base):
    __tablename__ = 'nickname'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    name = Column(String(255))


class SeasonClub(Base):
    __tablename__ = 'season_club'

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('season.id'))
    club_id = Column(Integer, ForeignKey('clubs.id'))
    rank = Column(Integer)
    win = Column(Integer)
    loss = Column(Integer)
    SRS = Column(Float)       
    pace = Column(Float)  
    relative_pace = Column(Float) 
    ORtg = Column(Float) 
    relative_ORtg = Column(Float)  
    DRtg = Column(Float) 
    relative_DRtg = Column(Float)


class SeasonPlayer(Base):
    __tablename__ = 'season_player'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season_id = Column(Integer, ForeignKey('season.id'))
    rank = Column(Integer)
    pts = Column(Integer)
    game = Column(Integer)
    minutes_played = Column(Integer)
    field_goals = Column(Integer)
    Attemps_field_goals = Column(Integer)
    assists = Column(Integer)
    block = Column(Integer)
    games_started = Column(Integer)
    total_rebounds = Column(Integer)
    steals = Column(Integer)
    turnovers = Column(Integer)
    personal_fouls =Column(Integer)
    effective_field_goal_percentage = Column(Float) 
    free_throw_percentage = Column(Float) 
 

class Award(Base):
    __tablename__ = 'awards'
    
    id = Column(Integer, primary_key=True)
    season_player_id = Column(Integer, ForeignKey('season_player.id'))
    name = Column(String(255))


class Highschool(Base):
    __tablename__ = 'highschool'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    city = Column(String(255))


class College(Base):
    __tablename__ = 'college'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class Position(Base):
    __tablename__ = 'position'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class PlayerPosition(Base):
    __tablename__ = 'player_position'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    position_id = Column(Integer, ForeignKey('position.id'))


class Coach(Base):
    __tablename__ = 'coach'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class CoachSeasonClub(Base):
    __tablename__ = 'coach_season_club'

    id = Column(Integer, primary_key=True)
    coach_id = Column(Integer, ForeignKey('coach.id'))
    club_season_id = Column(Integer, ForeignKey('season_club.id'))
    wins = Column(Integer)
    losses = Column(Integer)