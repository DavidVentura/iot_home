import { Router } from '@reach/router';

import Home from 'pages/Home';
import Navigation from 'components/Navigation';
import styles from './app.module.css';
import Rooms from 'pages/Rooms';
import Moods from 'pages/Moods';
import Stats from 'pages/Stats';

const App = () => {
  return (
    <div className={styles.app}>
      <div className={styles.main}>
        <Router>
          <Home path='/' />
          <Rooms path='/rooms' />
          <Moods path='/moods' />
          <Stats path='/stats' />
        </Router>
      </div>
      <div className={styles.navbar}>
        <Navigation/>
      </div>
    </div>
  );
}

export default App;
