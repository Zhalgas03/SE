"""
SQLAlchemy Model Usage Examples

This file demonstrates typical CRUD operations with the new trip management models.
Use these examples to validate integration and understand model usage.

Dependencies:
    - SQLAlchemy 2.0+
    - psycopg2-binary
    - python-dotenv
"""

from sqlalchemy import create_engine, sessionmaker
from sqlalchemy.orm import sessionmaker
from models.trip import Base, Trip, VotingRule, Vote, TripGroup, User, TripStatus, VoteType, UserRole
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (run once)
def create_tables():
    """Create all tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

# =============================================================================
# TRIP CRUD OPERATIONS
# =============================================================================

def create_trip_example():
    """Example: Create a new trip"""
    db = SessionLocal()
    try:
        # Create a new trip
        new_trip = Trip(
            name="Weekend Trip to Paris",
            description="A romantic weekend getaway to the City of Light",
            creator_id=1,  # Assuming user ID 1 exists
            date_start=datetime.now() + timedelta(days=30),
            date_end=datetime.now() + timedelta(days=32),
            status=TripStatus.DRAFT
        )
        
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        
        print(f"Created trip: {new_trip.name} (ID: {new_trip.id})")
        return new_trip
        
    except Exception as e:
        db.rollback()
        print(f"Error creating trip: {e}")
        raise
    finally:
        db.close()

def get_trip_example(trip_id: int):
    """Example: Get trip by ID with relationships"""
    db = SessionLocal()
    try:
        # Get trip with all relationships
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if trip:
            print(f"Trip: {trip.name}")
            print(f"Creator: {trip.creator.username if trip.creator else 'Unknown'}")
            print(f"Status: {trip.status}")
            print(f"Votes: {len(trip.votes)}")
            print(f"Members: {len(trip.trip_group)}")
        else:
            print(f"Trip {trip_id} not found")
            
        return trip
        
    finally:
        db.close()

def update_trip_example(trip_id: int):
    """Example: Update trip information"""
    db = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip:
            # Update trip details
            trip.name = "Updated: " + trip.name
            trip.description = "Updated description"
            trip.status = TripStatus.PENDING_VOTE
            
            db.commit()
            print(f"Updated trip: {trip.name}")
        else:
            print(f"Trip {trip_id} not found")
            
    except Exception as e:
        db.rollback()
        print(f"Error updating trip: {e}")
        raise
    finally:
        db.close()

def delete_trip_example(trip_id: int):
    """Example: Delete a trip (cascades to related records)"""
    db = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip:
            db.delete(trip)
            db.commit()
            print(f"Deleted trip: {trip.name}")
        else:
            print(f"Trip {trip_id} not found")
            
    except Exception as e:
        db.rollback()
        print(f"Error deleting trip: {e}")
        raise
    finally:
        db.close()

def list_trips_example(creator_id: int = None):
    """Example: List trips with filtering"""
    db = SessionLocal()
    try:
        query = db.query(Trip)
        
        if creator_id:
            query = query.filter(Trip.creator_id == creator_id)
        
        trips = query.order_by(Trip.created_at.desc()).all()
        
        for trip in trips:
            print(f"ID: {trip.id}, Name: {trip.name}, Status: {trip.status}")
            
        return trips
        
    finally:
        db.close()

# =============================================================================
# VOTING RULE CRUD OPERATIONS
# =============================================================================

def create_voting_rule_example(trip_id: int):
    """Example: Create voting rule for a trip"""
    db = SessionLocal()
    try:
        voting_rule = VotingRule(
            trip_id=trip_id,
            approval_threshold=0.75,  # 75% approval required
            min_votes_required=5,
            max_votes_allowed=20,
            duration_hours=48,
            rule_type='majority',
            voting_start=datetime.now(),
            voting_end=datetime.now() + timedelta(hours=48)
        )
        
        db.add(voting_rule)
        db.commit()
        db.refresh(voting_rule)
        
        print(f"Created voting rule for trip {trip_id}")
        return voting_rule
        
    except Exception as e:
        db.rollback()
        print(f"Error creating voting rule: {e}")
        raise
    finally:
        db.close()

def get_voting_rule_example(trip_id: int):
    """Example: Get voting rule for a trip"""
    db = SessionLocal()
    try:
        voting_rule = db.query(VotingRule).filter(VotingRule.trip_id == trip_id).first()
        
        if voting_rule:
            print(f"Voting Rule for Trip {trip_id}:")
            print(f"  Approval Threshold: {voting_rule.approval_threshold * 100}%")
            print(f"  Min Votes Required: {voting_rule.min_votes_required}")
            print(f"  Duration: {voting_rule.duration_hours} hours")
            print(f"  Rule Type: {voting_rule.rule_type}")
        else:
            print(f"No voting rule found for trip {trip_id}")
            
        return voting_rule
        
    finally:
        db.close()

# =============================================================================
# VOTE CRUD OPERATIONS
# =============================================================================

def create_vote_example(trip_id: int, user_id: int = None, session_token: str = None):
    """Example: Create a vote (authenticated user or guest)"""
    db = SessionLocal()
    try:
        vote = Vote(
            trip_id=trip_id,
            user_id=user_id,
            session_token=session_token,
            value=1,  # 1 for YES, -1 for NO
            comment="I'm excited about this trip!"
        )
        
        db.add(vote)
        db.commit()
        db.refresh(vote)
        
        voter = f"User {user_id}" if user_id else f"Guest ({session_token[:8]}...)"
        print(f"Created vote: {voter} voted YES on trip {trip_id}")
        return vote
        
    except Exception as e:
        db.rollback()
        print(f"Error creating vote: {e}")
        raise
    finally:
        db.close()

def get_votes_for_trip_example(trip_id: int):
    """Example: Get all votes for a trip"""
    db = SessionLocal()
    try:
        votes = db.query(Vote).filter(Vote.trip_id == trip_id).all()
        
        print(f"Votes for Trip {trip_id}:")
        for vote in votes:
            voter = f"User {vote.user_id}" if vote.user_id else f"Guest ({vote.session_token[:8]}...)"
            vote_text = "YES" if vote.value == 1 else "NO"
            print(f"  {voter}: {vote_text} - {vote.comment}")
            
        return votes
        
    finally:
        db.close()

def get_voting_status_example(trip_id: int):
    """Example: Get voting status using database function"""
    db = SessionLocal()
    try:
        # Use the database function we created
        result = db.execute(
            "SELECT * FROM get_trip_voting_status(%s)",
            (trip_id,)
        ).fetchone()
        
        if result:
            total_votes, yes_votes, no_votes, approval_pct, is_approved, voting_ended = result
            print(f"Voting Status for Trip {trip_id}:")
            print(f"  Total Votes: {total_votes}")
            print(f"  Yes Votes: {yes_votes}")
            print(f"  No Votes: {no_votes}")
            print(f"  Approval Percentage: {approval_pct}%")
            print(f"  Is Approved: {is_approved}")
            print(f"  Voting Ended: {voting_ended}")
        else:
            print(f"No voting data found for trip {trip_id}")
            
        return result
        
    finally:
        db.close()

# =============================================================================
# TRIP GROUP CRUD OPERATIONS
# =============================================================================

def add_user_to_trip_example(trip_id: int, user_id: int, role: UserRole = UserRole.MEMBER):
    """Example: Add user to trip group"""
    db = SessionLocal()
    try:
        trip_membership = TripGroup(
            trip_id=trip_id,
            user_id=user_id,
            role=role
        )
        
        db.add(trip_membership)
        db.commit()
        db.refresh(trip_membership)
        
        print(f"Added user {user_id} to trip {trip_id} as {role.value}")
        return trip_membership
        
    except Exception as e:
        db.rollback()
        print(f"Error adding user to trip: {e}")
        raise
    finally:
        db.close()

def get_trip_members_example(trip_id: int):
    """Example: Get all members of a trip"""
    db = SessionLocal()
    try:
        members = db.query(TripGroup).filter(TripGroup.trip_id == trip_id).all()
        
        print(f"Members of Trip {trip_id}:")
        for member in members:
            print(f"  User {member.user_id}: {member.role.value} (joined: {member.joined_at})")
            
        return members
        
    finally:
        db.close()

# =============================================================================
# ADVANCED QUERIES
# =============================================================================

def complex_trip_query_example():
    """Example: Complex query with joins and filtering"""
    db = SessionLocal()
    try:
        # Get trips with voting status and member count
        from sqlalchemy import func
        
        trips_with_stats = db.query(
            Trip,
            func.count(Vote.id).label('vote_count'),
            func.count(TripGroup.id).label('member_count')
        ).outerjoin(Vote).outerjoin(TripGroup).group_by(Trip.id).all()
        
        for trip, vote_count, member_count in trips_with_stats:
            print(f"Trip: {trip.name}")
            print(f"  Votes: {vote_count}, Members: {member_count}")
            print(f"  Status: {trip.status}")
            
        return trips_with_stats
        
    finally:
        db.close()

def search_trips_example(search_term: str):
    """Example: Search trips by name or description"""
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        
        trips = db.query(Trip).filter(
            or_(
                Trip.name.ilike(f"%{search_term}%"),
                Trip.description.ilike(f"%{search_term}%")
            )
        ).all()
        
        print(f"Search results for '{search_term}':")
        for trip in trips:
            print(f"  {trip.name}: {trip.description[:50]}...")
            
        return trips
        
    finally:
        db.close()

# =============================================================================
# INTEGRATION WITH EXISTING RAW SQL
# =============================================================================

def hybrid_approach_example():
    """Example: Using SQLAlchemy models alongside existing raw SQL"""
    db = SessionLocal()
    try:
        # Use SQLAlchemy for new operations
        trip = db.query(Trip).filter(Trip.id == 1).first()
        
        if trip:
            # Use raw SQL for complex operations (if needed)
            result = db.execute("""
                SELECT COUNT(*) as vote_count 
                FROM votes 
                WHERE trip_id = %s AND value = 1
            """, (trip.id,)).fetchone()
            
            print(f"Trip: {trip.name}")
            print(f"Yes votes (raw SQL): {result[0]}")
            print(f"Total votes (SQLAlchemy): {len(trip.votes)}")
            
    finally:
        db.close()

# =============================================================================
# USAGE PATTERNS
# =============================================================================

def typical_workflow_example():
    """Example: Complete workflow from trip creation to voting"""
    print("=== Complete Trip Workflow Example ===")
    
    # 1. Create trip
    trip = create_trip_example()
    
    # 2. Create voting rule
    voting_rule = create_voting_rule_example(trip.id)
    
    # 3. Add members
    add_user_to_trip_example(trip.id, 1, UserRole.CREATOR)
    add_user_to_trip_example(trip.id, 2, UserRole.MEMBER)
    add_user_to_trip_example(trip.id, 3, UserRole.MEMBER)
    
    # 4. Create votes
    create_vote_example(trip.id, user_id=2, session_token=None)
    create_vote_example(trip.id, user_id=None, session_token="guest_token_123")
    
    # 5. Check voting status
    get_voting_status_example(trip.id)
    
    # 6. Get trip details
    get_trip_example(trip.id)
    
    print("=== Workflow Complete ===")

if __name__ == "__main__":
    # Create tables first
    create_tables()
    
    # Run examples
    typical_workflow_example() 