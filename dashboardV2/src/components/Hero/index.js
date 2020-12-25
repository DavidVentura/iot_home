import React from 'react';
import dayjs from 'dayjs'
import styles from './hero.module.css';

const Hero = () => {
  const date = dayjs().format('DD ddd');
  return (
    <div className={styles.main}>
      <div className={styles.day}>
        <h1>{date}</h1>
        <h2>Pasta carbonara</h2>
      </div>
      <div className={styles.stats}>
        <h2>10°</h2>
        <h2>18° | 55%</h2>
      </div>
    </div>
  )
};

export default Hero;