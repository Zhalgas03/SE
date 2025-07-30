# Voting Time Limit Feature

## Overview
The voting time limit feature allows trip creators to set a specific duration for voting sessions, with automatic expiration and validation to ensure fair and time-bound voting processes.

## Features Implemented

### 1. Voting Session Duration Control
- **Duration Range**: 5 minutes to 24 hours (1440 minutes)
- **Default Duration**: 24 hours (1440 minutes)
- **Validation**: Server-side validation ensures durations are within acceptable limits

### 2. Automatic Expiration
- **Real-time Expiration**: Voting sessions automatically close when the deadline is reached
- **Status Tracking**: Active/expired status is calculated in real-time
- **No Further Votes**: Users cannot submit votes after expiration

### 3. Enhanced User Experience
- **Time Remaining Display**: Shows countdown timer for active voting sessions
- **Session Status**: Clear indication of voting session status (active/expired)
- **Duration Selection**: Modal interface for setting voting duration

## Database Schema Changes

### New Columns in `voting_rules` Table
```sql
-- Added columns for expiration tracking
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
expires_at TIMESTAMP
```

### Migration Applied
The existing schema fix script (`final_schema_audit_and_fix.py`) has been updated to:
1. Add `created_at` column with default current timestamp
2. Add `expires_at` column for expiration tracking
3. Update existing voting rules with default 24-hour expiration

## API Endpoints Updated

### 1. `POST /api/votes/start/<trip_id>` - Enhanced
**Purpose**: Start a voting session with specified duration

**Request Body**:
```json
{
  "duration_minutes": 60
}
```

**Validation**:
- Minimum: 5 minutes
- Maximum: 1440 minutes (24 hours)
- Must be a valid integer

**Response**:
```json
{
  "success": true,
  "link": "http://localhost:3000/vote/{trip_id}",
  "duration_minutes": 60,
  "expires_at": "2024-01-15T14:30:00"
}
```

**Error Responses**:
- `400`: Invalid duration (too short/long or invalid format)
- `401`: Authentication required
- `404`: Trip not found or user doesn't own it

### 2. `GET /api/votes/status/<trip_id>` - Enhanced
**Purpose**: Check voting status with expiration information

**Response**:
```json
{
  "success": true,
  "hasVoted": false,
  "voteValue": null,
  "votingActive": true,
  "expiresAt": "2024-01-15T14:30:00"
}
```

### 3. `POST /api/votes/<trip_id>` - Enhanced
**Purpose**: Submit a vote (with expiration check)

**New Validation**:
- Checks if voting session is active
- Rejects votes for expired sessions

**Error Responses**:
- `410`: Voting session has expired
- `404`: No voting session found for this trip

## Frontend Changes

### Enhanced VotingInterface Component

#### New State Variables
```javascript
const [votingActive, setVotingActive] = useState(false);
const [expiresAt, setExpiresAt] = useState(null);
const [timeRemaining, setTimeRemaining] = useState(null);
const [showDurationModal, setShowDurationModal] = useState(false);
const [durationMinutes, setDurationMinutes] = useState(60);
```

#### New Features
1. **Duration Selection Modal**: Allows users to set voting duration
2. **Real-time Countdown**: Shows time remaining for active sessions
3. **Session Status Display**: Shows different UI based on voting status
4. **Expiration Handling**: Prevents voting on expired sessions

#### UI States
1. **No Active Session**: Shows "Start Voting Session" button
2. **Active Session - Not Voted**: Shows voting buttons with countdown
3. **Active Session - Voted**: Shows vote result with time remaining
4. **Expired Session**: Shows "Voting session has ended" message

## Validation Rules

### Duration Validation
```python
# Backend validation in votes.py
if duration_minutes < 5:
    return jsonify(success=False, message="Voting duration must be at least 5 minutes"), 400
if duration_minutes > 1440:  # 24 hours
    return jsonify(success=False, message="Voting duration cannot exceed 24 hours"), 400
```

### Expiration Check
```python
# SQL query to check if voting is active
SELECT *, 
       CASE WHEN expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP 
       THEN 'active' ELSE 'expired' END as status
FROM voting_rules 
WHERE trip_id = %s
```

## Error Handling

### Backend Error Codes
- `400`: Invalid duration parameters
- `401`: Authentication required
- `404`: Trip not found or no voting session
- `410`: Voting session has expired
- `500`: Server error

### Frontend Error Handling
- Network error handling with user-friendly messages
- Validation error display
- Session expiration notifications

## Testing

### Test Files Created
1. `test_voting_time_limit.py`: Comprehensive testing of the new feature
2. Updated `final_schema_audit_and_fix.py`: Includes expiration column checks

### Test Coverage
- ✅ Duration validation (5 minutes to 24 hours)
- ✅ Expiration calculation and status logic
- ✅ Database operations with expiration
- ✅ Frontend state management
- ✅ Error handling scenarios

## Migration Notes

### Database Migration
The migration is handled by the existing schema fix script:
```python
# Check if created_at column exists
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'voting_rules' AND column_name = 'created_at'
""")
if not cur.fetchone():
    cur.execute("ALTER TABLE voting_rules ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

# Check if expires_at column exists
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'voting_rules' AND column_name = 'expires_at'
""")
if not cur.fetchone():
    cur.execute("ALTER TABLE voting_rules ADD COLUMN expires_at TIMESTAMP")
```

### Backward Compatibility
- Existing voting rules are updated with default 24-hour expiration
- Legacy voting endpoints continue to work
- No breaking changes to existing functionality

## Usage Examples

### Starting a Voting Session
```javascript
// Frontend: Start 1-hour voting session
const response = await fetch(`/api/votes/start/${tripId}`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ duration_minutes: 60 })
});
```

### Checking Voting Status
```javascript
// Frontend: Check if voting is active
const response = await fetch(`/api/votes/status/${tripId}`, {
  headers: { Authorization: `Bearer ${token}` }
});
const data = await response.json();
if (data.votingActive) {
  // Show voting interface
} else {
  // Show expired message
}
```

## Security Considerations

### Input Validation
- Duration parameters are validated server-side
- SQL injection protection through parameterized queries
- Authentication required for session creation

### Access Control
- Only trip creators can start voting sessions
- Users cannot vote on expired sessions
- Proper error messages without information leakage

## Performance Considerations

### Database Queries
- Efficient expiration checks using database timestamps
- Indexed queries on trip_id and expires_at
- Minimal additional database overhead

### Frontend Performance
- Real-time countdown updates every minute
- Efficient state management
- Minimal re-renders

## Future Enhancements

### Potential Improvements
1. **Email Notifications**: Notify users when voting sessions are about to expire
2. **Automatic Extensions**: Allow extending voting sessions
3. **Multiple Sessions**: Support for multiple voting rounds
4. **Analytics**: Track voting session statistics
5. **Custom Durations**: Allow custom duration presets

### Configuration Options
- Configurable minimum/maximum durations
- Default duration settings per user/organization
- Timezone handling for global users

## Troubleshooting

### Common Issues
1. **Voting session not starting**: Check authentication and trip ownership
2. **Duration validation errors**: Ensure duration is between 5-1440 minutes
3. **Expired sessions**: Check server time and database timestamps
4. **Frontend countdown issues**: Verify timezone settings

### Debug Information
- Backend logs include detailed voting session information
- Frontend console logs show voting status updates
- Database queries can be monitored for expiration checks

## Conclusion

The voting time limit feature provides a robust, user-friendly solution for time-bound voting sessions. It maintains backward compatibility while adding essential functionality for fair and controlled voting processes. The implementation includes comprehensive validation, error handling, and user experience enhancements. 