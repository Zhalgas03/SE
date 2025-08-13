// src/components/AccountLeft.jsx
import React, { useState } from 'react';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

function AccountLeft({
  username,
  email,
  enable2FA,
  message,

  editingUsername,
  setEditingUsername,
  editingEmail,
  setEditingEmail,

  setUsername,
  setEmail,

  onSave,
  isSaving,

  onToggle2FA,
  isToggling2FA,

  currentPassword,
  setCurrentPassword,
  newPassword,
  setNewPassword,
  onChangePassword,
  isChangingPassword,

  // 👇 новые пропсы
  isPremium,
  weeklyTripOptIn,
  onToggleWeeklyTrip,
  isTogglingWeekly,
}) {
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);

  return (
    <div className="card shadow-sm rounded-4 p-4">
      <h4 className="mb-4 fw-bold">Account Settings</h4>

      {message && <div className="alert alert-info">{message}</div>}

      {/* Username */}
      <div className="mb-3">
        <label className="form-label">Username</label>
        {!editingUsername ? (
          <div
            className="form-control bg-light"
            style={{ cursor: 'pointer' }}
            onClick={() => setEditingUsername(true)}
            title="Click to edit"
          >
            {username || '—'}
          </div>
        ) : (
          <input
            type="text"
            className="form-control"
            placeholder={username}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onBlur={() => setEditingUsername(false)}
            autoFocus
          />
        )}
      </div>

      {/* Email */}
      <div className="mb-3">
        <label className="form-label">Email</label>
        {!editingEmail ? (
          <div
            className="form-control bg-light"
            style={{ cursor: 'pointer' }}
            onClick={() => setEditingEmail(true)}
            title="Click to edit"
          >
            {email || '—'}
          </div>
        ) : (
          <input
            type="email"
            className="form-control"
            placeholder={email}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => setEditingEmail(false)}
            autoFocus
          />
        )}
      </div>

      {/* 2FA */}
      <div className="form-check form-switch mb-3 d-flex align-items-center gap-3">
        <input
          className="form-check-input"
          type="checkbox"
          id="enable2FA"
          checked={enable2FA}
          onChange={onToggle2FA}
          disabled={isToggling2FA}
        />
        <label className="form-check-label mb-0" htmlFor="enable2FA">
          Enable Two-Factor Authentication (2FA)
        </label>
        {isToggling2FA && (
          <div
            className="spinner-border spinner-border-sm text-secondary ms-2"
            role="status"
            style={{ width: '1rem', height: '1rem' }}
          />
        )}
      </div>

      {/* Weekly AI Trip (только для Premium) */}
      <div className="form-check form-switch mb-4 d-flex align-items-center gap-3">
        <input
          className="form-check-input"
          type="checkbox"
          id="weeklyTripOptIn"
          checked={!!weeklyTripOptIn}
          onChange={onToggleWeeklyTrip}
          disabled={!isPremium || isTogglingWeekly}
          title={isPremium ? 'Toggle weekly AI trip emails' : 'Premium only'}
        />
        <label className="form-check-label mb-0" htmlFor="weeklyTripOptIn">
          Weekly AI Trip plan
          {!isPremium && (
            <span className="ms-2 badge text-bg-secondary">Premium only</span>
          )}
        </label>
        {isTogglingWeekly && (
          <div
            className="spinner-border spinner-border-sm text-secondary ms-2"
            role="status"
            style={{ width: '1rem', height: '1rem' }}
          />
        )}
      </div>

      <button
        onClick={onSave}
        className="btn btn-primary w-100"
        disabled={isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </button>

      {/* Change password */}
      <hr className="my-4" />
      <h5 className="fw-bold mb-3">Change Password</h5>

      <div className="mb-3 position-relative">
        <label className="form-label">Current Password</label>
        <input
          type={showCurrentPassword ? 'text' : 'password'}
          className="form-control pe-5"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
        <span
          className="position-absolute"
          style={{
            top: '70%',
            right: '12px',
            transform: 'translateY(-50%)',
            cursor: 'pointer',
            color: '#888',
            fontSize: '1.1rem',
            lineHeight: '1',
          }}
          onClick={() => setShowCurrentPassword((v) => !v)}
        >
          {showCurrentPassword ? <FaEyeSlash /> : <FaEye />}
        </span>
      </div>

      <div className="mb-3 position-relative">
        <label className="form-label">New Password</label>
        <input
          type={showNewPassword ? 'text' : 'password'}
          className="form-control pe-5"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
        <span
          className="position-absolute"
          style={{
            top: '70%',
            right: '12px',
            transform: 'translateY(-50%)',
            cursor: 'pointer',
            color: '#888',
            fontSize: '1.1rem',
            lineHeight: '1',
          }}
          onClick={() => setShowNewPassword((v) => !v)}
        >
          {showNewPassword ? <FaEyeSlash /> : <FaEye />}
        </span>
      </div>

      <button
        onClick={onChangePassword}
        className="btn btn-outline-dark w-100"
        disabled={isChangingPassword}
      >
        {isChangingPassword ? 'Changing...' : 'Change Password'}
      </button>
    </div>
  );
}

export default AccountLeft;
