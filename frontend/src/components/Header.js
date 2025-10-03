import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="logo">
        <h1>StratoSenseSense</h1>
        <p>Air Quality Prediction & Monitoring</p>
      </div>
      <nav className="nav">
        <ul>
          <li><a href="#dashboard">Dashboard</a></li>
          <li><a href="#map">Map View</a></li>
          <li><a href="#predictions">Predictions</a></li>
          <li><a href="#about">About</a></li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;
