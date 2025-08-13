import React from 'react';

function AccountRight({ isSubscribed, onSubscribe, isDarkTheme, isPremium }) {
  if (isSubscribed || isPremium) {
    return (
      <div className="alert alert-success mt-3 text-center fw-semibold fs-5">
        🎉 Вы уже на Premium
      </div>
    );
  }

  return (
    <div className="premium-wrapper-light p-4 rounded-4 bg-white shadow-sm">
      <h4 className="mb-4 text-center fw-bold fs-4 text-dark">Upgrade to Premium</h4>

      <div className="row row-cols-1 row-cols-md-2 g-2">
        {/* Individual */}
        <div className="col">
          <div className="premium-card-light d-flex flex-column rounded-4 p-4 h-100 border text-start">
            <img
              src={isDarkTheme ? 'premium_alt.png' : 'premium.png'}
              alt="Premium"
              className="logo-premium"
            />
            <h4 className="fw-bold text-primary">Individual</h4>
            <p className="text-muted mb-3">€5.00 / month</p>
            <hr />
            <ul className="list-unstyled mb-4 small text-dark">
              <li>• 1 Premium account</li>
              <li>• Weekly AI travel plans</li>
              <li>• Voting access & early features</li>
              <li>• Cancel anytime</li>
            </ul>

            {isPremium ? (
              <button className="btn btn-secondary rounded-pill fw-semibold mt-auto" disabled>
                Ваш план
              </button>
            ) : (
              <button
                className="btn btn-primary rounded-pill fw-semibold mt-auto"
                onClick={onSubscribe}
              >
                Get Premium
              </button>
            )}

            <p className="mt-3 text-muted small">
              €0 for 1 month, then €5.00/month after. Cancel anytime.
            </p>
          </div>
        </div>

        {/* Duo */}
        <div className="col">
          <div className="premium-card-light d-flex flex-column rounded-4 p-4 h-100 border text-start">
            <img
              src={isDarkTheme ? 'premium_alt.png' : 'premium.png'}
              alt="Premium"
              className="logo-premium"
            />
            <h4 className="fw-bold text-success">Duo</h4>
            <p className="text-muted mb-3">€8.00 / month</p>
            <hr />
            <ul className="list-unstyled mb-4 small text-dark">
              <li>• 2 Premium accounts</li>
              <li>• Shared AI travel planner</li>
              <li>• Early access features</li>
              <li>• Cancel anytime</li>
            </ul>
            <button className="btn btn-outline-success rounded-pill fw-semibold mt-auto" disabled>
              Coming Soon
            </button>
            <p className="mt-3 text-muted small">
              For couples who live together. Available soon.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


export default AccountRight;
