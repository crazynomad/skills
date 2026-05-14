import type { Page } from '@open-slide/core';

// Verbatim from themes/dark-coral.md. Mirror of dark-teal — only accent color differs.

const TopRow = ({
  left,
  right,
  leftColor = '#6B6B6B',
  rightColor = '#FF6B47',
}: {
  left: React.ReactNode;
  right: React.ReactNode;
  leftColor?: string;
  rightColor?: string;
}) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <p style={{ fontSize: 24, letterSpacing: 8, fontWeight: 300, color: leftColor, margin: 0 }}>
      {left}
    </p>
    <p style={{ fontSize: 24, letterSpacing: 5, fontWeight: 300, color: rightColor, margin: 0 }}>
      {right}
    </p>
  </div>
);

const BottomRow = ({ left, right }: { left: React.ReactNode; right: React.ReactNode }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
    <p style={{ fontSize: 21, color: '#6B6B6B', letterSpacing: 3, margin: 0 }}>{left}</p>
    <p style={{ fontSize: 21, color: '#6B6B6B', letterSpacing: 3, margin: 0 }}>{right}</p>
  </div>
);

const Accent = ({ children }: { children: React.ReactNode }) => (
  <span style={{ color: '#FF6B47' }}>{children}</span>
);

const fill = {
  width: '100%',
  height: '100%',
  background: '#0A0A0A',
  color: '#F5F2EB',
  fontFamily: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
  padding: '112px 128px 96px 128px',
  display: 'flex',
  flexDirection: 'column' as const,
  boxSizing: 'border-box' as const,
};

const Cover: Page = () => (
  <div style={fill}>
    <TopRow left="GREENTRAIN · DARK CORAL DEMO" right="01 / 03" />

    <div style={{ marginTop: 'auto', marginBottom: 'auto' }}>
      <p style={{ fontSize: 37, color: '#8A8A8A', letterSpacing: 5, margin: '0 0 26px 0' }}>
        NARRATIVE CHAPTER · WARM PALETTE
      </p>
      <h1 style={{ fontSize: 160, fontWeight: 700, lineHeight: 1.15, margin: 0, color: '#F5F2EB' }}>
        温度 与 <Accent>火光</Accent>。<br />
        纸页 翻动 的 声音。
      </h1>
      <p style={{ fontSize: 43, color: '#D4A574', lineHeight: 1.4, margin: '26px 0 0 0' }}>
        Dark Coral — 人文叙事 / 商业故事章节的暖色主题
      </p>
    </div>

    <BottomRow left="THEME · DARK CORAL" right="VISUAL-DECK · GREENTRAIN" />
  </div>
);

const Content: Page = () => (
  <div style={fill}>
    <TopRow left="THE MIRROR · OF DARK TEAL" right="02 / 03" />

    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <p style={{ fontSize: 60, fontWeight: 700, color: '#F5F2EB', margin: 0, lineHeight: 1.2 }}>
        一对镜像主题,<Accent>切换只换情绪</Accent>。
      </p>
      <ul style={{ fontSize: 32, lineHeight: 1.7, marginTop: 64, paddingLeft: 48, color: '#F5F2EB', fontWeight: 300 }}>
        <li>字号、padding、letter-spacing — <strong>完全一致</strong></li>
        <li>Layout helper(TopRow / BottomRow / Title) — <strong>共用</strong></li>
        <li>唯一改动:<strong style={{ color: '#FF6B47' }}>Accent</strong> 从 teal 换 coral</li>
        <li>同一份 deck,改 accent 一个变量就能换调性</li>
      </ul>
    </div>

    <BottomRow left="Mirror palette · single switch" right="Page 02" />
  </div>
);

const Closer: Page = () => (
  <div style={fill}>
    <TopRow left="THEME · APPLIED" right="03 / 03" />

    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
      }}
    >
      <p style={{ fontSize: 96, fontWeight: 700, color: '#F5F2EB', lineHeight: 1.2, margin: 0 }}>
        Coral 是 <Accent>火光</Accent>,<br />
        不是 霓虹灯。
      </p>
      <p
        style={{
          fontSize: 32,
          color: '#D4A574',
          letterSpacing: 5,
          marginTop: 96,
          fontStyle: 'italic',
        }}
      >
        一页 1-2 处 · 不要让暖色刷屏
      </p>
    </div>

    <BottomRow left="Theme demo · end" right="VISUAL-DECK 1.0" />
  </div>
);

export default [Cover, Content, Closer];
