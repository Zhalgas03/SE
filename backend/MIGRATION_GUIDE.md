# Trip Management System - Migration Guide

## Overview

This guide covers the safe migration to create SQLAlchemy models and database tables for the trip management system. The migration is **additive only** and will not modify or drop any existing data.

## Files Created

### 1. SQLAlchemy Models (`backend/models/trip.py`)
- **Trip**: Main trip entity with creator relationship
- **VotingRule**: Voting configuration for trips
- **Vote**: Individual votes (supports both users and guests)
- **TripGroup**: Many-to-many relationship between users and trips
- **User**: User model with trip relationships

### 2. Migration Script (`backend/migrations/001_create_trip_tables.sql`)
- Safe SQL migration that checks for table existence
- Creates all necessary tables, enums, indexes, and constraints
- Includes helper functions for voting logic

### 3. Migration Runner (`backend/run_migration.py`)
- Python script to safely execute the migration
- Includes error handling and validation
- Logs all operations for debugging

## Model Details

### Trip Model
```python
class Trip(Base):
    __tablename__ = 'trips'
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Dates and status
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    status = Column(Enum(TripStatus), default=TripStatus.DRAFT)
    
    # PDF file support (for /api/save_trip)
    pdf_file_path = Column(String(500))
    pdf_file_name = Column(String(255))
    pdf_file_size = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Key Features:**
- Matches existing raw SQL expectations (`creator_id`)
- Supports PDF file uploads
- Includes trip status tracking
- Auto-updating timestamps

### VotingRule Model
```python
class VotingRule(Base):
    __tablename__ = 'voting_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False, unique=True)
    
    # Voting configuration
    approval_threshold = Column(Float, nullable=False, default=0.7)
    min_votes_required = Column(Integer, nullable=False, default=3)
    max_votes_allowed = Column(Integer)
    duration_hours = Column(Integer, nullable=False, default=24)
    rule_type = Column(String(50), default='majority')
    
    # Optional explicit voting period
    voting_start = Column(DateTime)
    voting_end = Column(DateTime)
```

**Key Features:**
- One rule per trip (unique constraint)
- Flexible voting thresholds
- Support for explicit voting periods
- Configurable vote limits

### Vote Model
```python
class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False)
    
    # Voter identification (either user_id OR session_token)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_token = Column(String(255))
    
    # Vote data
    value = Column(Integer, nullable=False)  # 1 for YES, -1 for NO
    comment = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
```

**Key Features:**
- Supports both authenticated users and guest voting
- One vote per user/token per trip
- Includes optional comments
- Integer vote values (1/-1) for easy calculations

### TripGroup Model
```python
class TripGroup(Base):
    __tablename__ = 'trip_group'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    joined_at = Column(DateTime, default=func.now())
```

**Key Features:**
- Many-to-many relationship between users and trips
- User roles (creator, member, admin)
- Tracks when users joined trips

## Database Schema

### Tables Created
1. **trips** - Main trip entity
2. **voting_rules** - Voting configuration
3. **votes** - Individual votes
4. **trip_group** - User-trip relationships

### Enums Created
1. **trip_status** - draft, pending_vote, approved, rejected, cancelled
2. **vote_type** - yes, no
3. **user_role** - creator, member, admin

### Indexes Created
- Performance indexes on foreign keys
- Indexes on frequently queried columns
- Composite indexes for unique constraints

### Constraints
- Foreign key constraints with CASCADE delete
- Check constraints for data validation
- Unique constraints to prevent duplicates
- Date validation (end >= start)

## Helper Functions

### get_trip_voting_status(trip_id)
Returns voting statistics and status:
- Total votes, yes votes, no votes
- Approval percentage
- Whether trip is approved
- Whether voting has ended

### can_user_vote_on_trip(trip_id, user_id, session_token)
Checks if a user can vote:
- Verifies voting hasn't ended
- Ensures user hasn't already voted
- Supports both authenticated and guest voting

### update_updated_at_column()
Trigger function to auto-update `updated_at` timestamps.

## Migration Safety Features

### Additive Only
- Checks for table existence before creating
- Skips existing tables without error
- No DROP or ALTER operations on existing data

### Transaction Safety
- Wrapped in BEGIN/COMMIT transaction
- Automatic rollback on errors
- Detailed logging of all operations

### Validation
- Verifies all tables were created
- Checks enum types and functions
- Validates indexes and constraints

## Installation Steps

### 1. Install Dependencies
```bash
pip install sqlalchemy psycopg2-binary python-dotenv
```

### 2. Set Environment Variables
```bash
# Option 1: DATABASE_URL
export DATABASE_URL="postgresql://user:password@host:port/database"

# Option 2: Individual variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=your_database
export DB_USER=your_user
export DB_PASSWORD=your_password
```

### 3. Run Migration
```bash
cd backend
python run_migration.py
```

### 4. Verify Migration
Check the migration log:
```bash
cat migration.log
```

Expected output:
```
INFO - Migration completed successfully!
INFO - Created tables: trips, voting_rules, votes, trip_group
INFO - Created enums: trip_status, vote_type, user_role
INFO - Created functions: get_trip_voting_status, can_user_vote_on_trip, update_updated_at_column
```

## Integration with Existing Code

### Raw SQL Compatibility
The models are designed to work with existing raw SQL:
- Same column names and types
- Compatible foreign key relationships
- Matching data constraints

### API Compatibility
All existing API endpoints will continue to work:
- `/api/trips` - Trip creation and retrieval
- `/api/voting_rules` - Voting rule management
- `/api/votes` - Vote submission and retrieval

### Gradual Migration Path
1. Run migration (creates tables alongside existing ones)
2. Test new functionality with SQLAlchemy models
3. Gradually migrate API endpoints to use models
4. Remove old raw SQL when confident

## Troubleshooting

### Common Issues

**Connection Errors:**
- Verify database credentials
- Check network connectivity
- Ensure database is running

**Permission Errors:**
- Verify user has CREATE TABLE permissions
- Check schema ownership

**Migration Already Run:**
- Safe to run multiple times
- Existing tables will be skipped
- Check logs for details

### Log Files
- `migration.log` - Detailed execution log
- Database logs - PostgreSQL server logs

### Rollback
Since this is additive only, no rollback is needed. If you need to remove tables:
```sql
DROP TABLE IF EXISTS trip_group, votes, voting_rules, trips CASCADE;
DROP TYPE IF EXISTS trip_status, vote_type, user_role CASCADE;
```

## Next Steps

After successful migration:

1. **Test Models**: Create test scripts to verify model functionality
2. **Update APIs**: Gradually migrate endpoints to use SQLAlchemy
3. **Add Features**: Implement new trip management features
4. **Performance**: Monitor and optimize database queries
5. **Documentation**: Update API documentation with new endpoints

## Support

For issues or questions:
1. Check the migration log file
2. Verify environment variables
3. Test database connectivity
4. Review PostgreSQL server logs 