import React from 'react';
import ThemeToggle from './ThemeToggle';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="logo">
        <h1>NOVA</h1>
        <p>Air Quality Prediction & Monitoring</p>
      </div>
      <div className="header-actions">
        <nav className="nav">
          <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#map">Map View</a></li>
            <li><a href="#predictions">Predictions</a></li>
            <li><a href="#about">About</a></li>
          </ul>
        </nav>
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;
