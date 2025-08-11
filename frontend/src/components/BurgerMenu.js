import React from 'react';
import './BurgerMenu.css';

function BurgerMenu({ isOpen, toggle }) {
  return (
    <button
      className="burger-button"
      onClick={toggle}
      aria-label="Toggle navigation"
    >
      <div className={`bar ${isOpen ? 'open top' : ''}`}></div>
      <div className={`bar ${isOpen ? 'open middle' : ''}`}></div>
      <div className={`bar ${isOpen ? 'open bottom' : ''}`}></div>
    </button>
  );
}

export default BurgerMenu;
