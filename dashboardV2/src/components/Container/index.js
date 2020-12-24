import React from 'react';
import cs from 'classnames';

import styles from './container.module.css';

const Container = ({ children, rounded, shadow }) => {
  return (
    <div className={cs(
      styles.main,
      {
        [styles.roundBorder]: rounded,
        [styles.shadow]: shadow
      })}
    >{children}</div>
  )
}

export default Container;