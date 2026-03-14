// @ts-check
// docusaurus.config.js — Small ISP Containerlab Docs

const { themes: prismThemes } = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Small ISP Lab',
  tagline: 'Nokia BNG · Containerlab · Automatización de Red',
  favicon: 'img/favicon.ico',

  url: 'https://abelperezr.github.io',
  baseUrl: '/small-isp-lab/',

  organizationName: 'abelperezr',
  projectName: 'small-isp-lab',

  onBrokenLinks: 'warn',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    localeConfigs: {
      es: {
        label: 'Español',
        htmlLang: 'es',
      },
      en: {
        label: 'English',
        htmlLang: 'en',
      },
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: 'docs',
          showLastUpdateTime: false,
          showLastUpdateAuthor: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // ── Social card ────────────────────────────────────────────
      image: 'img/social-card.png',

      // ── Color mode ─────────────────────────────────────────────
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },

      // ── Navbar ─────────────────────────────────────────────────
      navbar: {
        // hideOnScroll: true,  // optional — uncomment to hide on scroll
        logo: {
          // FIX: give the logo explicit alt and reasonable width so it
          // never bleeds over the nav items.
          alt: 'Small ISP Lab',
          src: 'img/logo.svg',           // light mode
          srcDark: 'img/logo-dark.svg',  // dark mode (same file is fine)
          width: 32,   // ← explicit px cap — prevents the logo from growing
          height: 32,
          href: '/',
          target: '_self',
        },
        title: 'Small ISP Lab',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Inicio',
          },
          {
            type: 'dropdown',
            label: 'Topo',
            position: 'left',
            items: [
              { to: '/docs/topologia/', label: 'Vista General' },
              { to: '/docs/topologia/underlay/', label: 'Underlay' },
              { to: '/docs/topologia/overlay/', label: 'Overlay' },
              { to: '/docs/topologia/bgp/', label: 'BGP' },
              { to: '/docs/topologia/srrp/', label: 'SRRP' },
              { to: '/docs/topologia/flujo-autenticacion/', label: 'Auth Flow' },
            ],
          },
          {
            type: 'dropdown',
            label: 'MOPT',
            position: 'left',
            items: [
              { to: '/docs/mopt/', label: 'Vista General' },
              { to: '/docs/mopt/bng-master/', label: 'BNG Master' },
              { to: '/docs/mopt/bng-slave/', label: 'BNG Slave' },
              { to: '/docs/mopt/olt/', label: 'OLT' },
              { to: '/docs/mopt/ont1/', label: 'ONT1' },
              { to: '/docs/mopt/ont2/', label: 'ONT2' },
              { to: '/docs/mopt/carrier1/', label: 'Carrier1' },
              { to: '/docs/mopt/carrier2/', label: 'Carrier2' },
              { to: '/docs/mopt/dns64/', label: 'DNS64' },
              { to: '/docs/mopt/lig/', label: 'LEA/LIG' },
            ],
          },
          {
            type: 'dropdown',
            label: 'Telem',
            position: 'left',
            items: [
              { to: '/docs/telemetria/', label: 'Vista General' },
              { to: '/docs/telemetria/gnmic/', label: 'gNMIc' },
              { to: '/docs/telemetria/prometheus/', label: 'Prometheus' },
              { to: '/docs/telemetria/grafana/', label: 'Grafana' },
            ],
          },
          {
            type: 'dropdown',
            label: 'LOGs',
            position: 'left',
            items: [
              { to: '/docs/logs/', label: 'Vista General' },
              { to: '/docs/logs/dashboard/', label: 'Dashboard e Integración' },
            ],
          },
          {
            type: 'dropdown',
            label: 'Radius',
            position: 'left',
            items: [
              { to: '/docs/radius/', label: 'Vista General' },
              { to: '/docs/radius/usuarios/', label: 'Usuarios' },
            ],
          },
          {
            type: 'dropdown',
            label: 'LEA',
            position: 'left',
            items: [
              { to: '/docs/lea-console/', label: 'Vista General' },
              { to: '/docs/lea-console/arquitectura/', label: 'Arquitectura' },
              { to: '/docs/lea-console/integracion/', label: 'Integración' },
              { to: '/docs/lea-console/ejecucion/', label: 'Ejecución' },
            ],
          },
          {
            type: 'dropdown',
            label: 'Cbot',
            position: 'left',
            items: [
              { to: '/docs/containerbot/', label: 'Vista General' },
              { to: '/docs/containerbot/telegram/', label: 'Telegram' },
              { to: '/docs/containerbot/operacion/', label: 'Operación' },
            ],
          },
          {
            type: 'dropdown',
            label: 'Operaciones',
            position: 'left',
            items: [
              { to: '/docs/operacion/runbook/', label: 'Vista General' },
              { to: '/docs/operacion/runbook/', label: 'Runbook' },
            ],
          },
          {
            type: 'dropdown',
            label: 'ATP',
            position: 'left',
            items: [
              {
                to: '/docs/atp/',
                label: 'Vista General',
              },
              {
                to: '/docs/atp/bng-baseline/',
                label: '1. Validación base de BNG',
              },
              {
                to: '/docs/atp/carriers-baseline/',
                label: '2. Validación base de Carriers',
              },
              {
                to: '/docs/atp/olt-baseline/',
                label: '3. Validación base de OLT',
              },
              {
                to: '/docs/atp/services-l2-l3/',
                label: '4. Servicios L2/L3',
              },
              {
                to: '/docs/atp/qos/',
                label: '5. QoS',
              },
              {
                to: '/docs/atp/srrp-bgp/',
                label: '6. SRRP y BGP',
              },
              {
                to: '/docs/atp/esm/',
                label: '7. ESM',
              },
              {
                to: '/docs/atp/cgnat/',
                label: '8. CGNAT',
              },
              {
                to: '/docs/atp/nat64/',
                label: '9. NAT64',
              },
              {
                to: '/docs/atp/ont/',
                label: '10. Pruebas ONT',
              },
              {
                to: '/docs/atp/lea-validation/',
                label: '11. LEA y LI',
              },
              {
                to: '/docs/atp/observability/',
                label: '12. Observabilidad',
              },
              {
                to: '/docs/atp/srrp-subscribers-demo/',
                label: '13. Failover Suscriptores SRRP',
              },
              {
                to: '/docs/atp/final-boss/',
                label: '14. Final Boss',
              },
            ],
          },
          {
            type: 'dropdown',
            label: 'Despliegue',
            position: 'left',
            items: [
              { to: '/docs/despliegue/instalacion/', label: 'Instalación' },
              { to: '/docs/despliegue/requisitos/', label: 'Requisitos' },
            ],
          },
          // ── Right-side items ─────────────────────────────────
          {
            type: 'search',
            position: 'right',
          },
          {
            type: 'localeDropdown',
            position: 'right',
          },
          {
            href: 'https://github.com/abelperezr/small-isp-lab',
            position: 'right',
            className: 'header-github-link',
            'aria-label': 'GitHub',
          },
        ],
      },

      // ── Footer ──────────────────────────────────────────────────
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentación',
            items: [
              { label: 'Inicio', to: '/docs' },
              { label: 'Despliegue', to: '/docs/despliegue/instalacion' },
            ],
          },
          {
            title: 'Lab',
            items: [
              { label: 'Topología', to: '/docs/topologia/' },
              { label: 'Telemetría', to: '/docs/telemetria/' },
              { label: 'ATP', to: '/docs/atp/' },
            ],
          },
          {
            title: 'Recursos',
            items: [
              { label: 'GitHub', href: 'https://github.com/abelperezr/small-isp-lab' },
              { label: 'YouTube @networkblade', href: 'https://youtube.com/@networkblade' },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Abel Pérez — Small ISP Lab · Built with Docusaurus`,
      },

      // ── Prism syntax highlight ───────────────────────────────────
      prism: {
        theme: prismThemes.vsLight,
        darkTheme: prismThemes.vsDark,
        additionalLanguages: ['bash', 'python', 'yaml', 'json', 'diff', 'nginx'],
      },

      // ── Algolia search (fill when ready) ────────────────────────
      // algolia: {
      //   appId: 'YOUR_APP_ID',
      //   apiKey: 'YOUR_SEARCH_API_KEY',
      //   indexName: 'small-isp-lab',
      // },

      // ── Docs metadata ────────────────────────────────────────────
      docs: {
        sidebar: {
          hideable: true,
          autoCollapseCategories: true,
        },
      },
    }),
};

module.exports = config;
