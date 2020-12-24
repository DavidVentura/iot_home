import Hero from 'components/Hero';
import Container from 'components/Container';
import styles from './app.module.css';

const App = () => {
  return (
    <div className={styles.main}>
      <Container rounded shadow>
        <Hero/>
      </Container>
    </div>
  );
}

export default App;
