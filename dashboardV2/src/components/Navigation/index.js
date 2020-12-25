import React from 'react';
import cs from 'classnames';
import { Link } from '@reach/router';

import { ReactComponent as HomeIcon } from 'icons/hero/home.svg';
import { ReactComponent as RoomsIcon } from 'icons/hero/template.svg';
import { ReactComponent as MoodsIcon } from 'icons/hero/heart.svg';
import { ReactComponent as StatsIcon } from 'icons/hero/chart-bar.svg';

import styles from './navigation.module.css';

const NavigationLink = ({ children, ...props }) => (
  <Link {...props} getProps={({ isCurrent }) => ({
    className: cs(styles.navigationLink, isCurrent && styles.navigationLinkActive)
  })}>
    {children}
  </Link>
)
const Navigation = () => {
  return (
    <nav className={styles.container}>
      <ul className={styles.navigation}>
        <li className={styles.navigationItem}>
          <NavigationLink to='/'>
            <HomeIcon/>
            home
          </NavigationLink>
        </li>
        <li className={styles.navigationItem}>
          <NavigationLink to='/rooms'>
            <RoomsIcon />
            rooms
          </NavigationLink>
        </li>
        <li className={styles.navigationItem}>
          <NavigationLink to='/moods'>
            <MoodsIcon />
            moods
          </NavigationLink>
        </li>
        <li className={styles.navigationItem}>
          <NavigationLink to='/stats'>
            <StatsIcon />
            stats
          </NavigationLink>
        </li>
      </ul>
    </nav>
  )
}

export default Navigation;