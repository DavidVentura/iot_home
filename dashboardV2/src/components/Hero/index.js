import React from 'react';

import styles from './hero.module.css';

const Hero = () => {
  return (
    <div className={styles.main}>
      <div className={styles.day}>
        24 dec
      </div>
      <div className={styles.stats}></div>
    </div>
  )
};

export default Hero;