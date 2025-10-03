import React from 'react';
import './App.css';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import MapView from './components/MapView';

function App() {
  return (
    <div className="App">
      <Header />
      <main className="main-content">
        <section id="dashboard">
          <Dashboard />
        </section>
        <section id="map">
          <MapView />
        </section>
      </main>
    </div>
  );
}

export default App;