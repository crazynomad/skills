import type { Page } from '@open-slide/core';

// Verbatim from themes/dark-teal.md. Keep this demo and the markdown in lockstep.

const TopRow = ({
  left,
  right,
  leftColor = '#6B6B6B',
  rightColor = '#76C7C0',
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
  <span style={{ color: '#76C7C0' }}>{children}</span>
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
    <TopRow left="GREENTRAIN · DARK TEAL DEMO" right="01 / 03" />

    <div style={{ marginTop: 'auto', marginBottom: 'auto' }}>
      <p style={{ fontSize: 37, color: '#8A8A8A', letterSpacing: 5, margin: '0 0 26px 0' }}>
        TECHNICAL CHAPTER · COOL PALETTE
      </p>
      <h1 style={{ fontSize: 160, fontWeight: 700, lineHeight: 1.15, margin: 0, color: '#F5F2EB' }}>
        理性 与 <Accent>克制</Accent>。<br />
        档案室 的 灯光。
      </h1>
      <p style={{ fontSize: 43, color: '#D4A574', lineHeight: 1.4, margin: '26px 0 0 0' }}>
        Dark Teal — 技术解读 / 研究简报章节的默认主题
      </p>
    </div>

    <BottomRow left="THEME · DARK TEAL" right="VISUAL-DECK · GREENTRAIN" />
  </div>
);

const Content: Page = () => (
  <div style={fill}>
    <TopRow
      left="THE PALETTE · 4+1 TONES"
      leftColor="#76C7C0"
      right="02 / 03"
      rightColor="#6B6B6B"
    />

    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <p style={{ fontSize: 60, fontWeight: 700, color: '#F5F2EB', margin: 0, lineHeight: 1.2 }}>
        一份 deck,只需要 <Accent>5 个色</Accent>。
      </p>
      <ul style={{ fontSize: 32, lineHeight: 1.7, marginTop: 64, paddingLeft: 48, color: '#F5F2EB', fontWeight: 300 }}>
        <li><strong style={{ color: '#76C7C0' }}>Teal</strong> — 理性、技术、被审判的对象</li>
        <li><strong style={{ color: '#D4A574' }}>Gold</strong> — 温度、副线、人文回声</li>
        <li><strong style={{ color: '#FF6B47' }}>Hot</strong> — 应急。一份 deck 最多用 2-3 次</li>
        <li><strong style={{ color: '#8A8A8A' }}>Muted/Dim/Faint</strong> — 灰阶三档,做层次</li>
      </ul>
    </div>

    <BottomRow left="Color hierarchy · not decoration" right="Page 02" />
  </div>
);

const Closer: Page = () => (
  <div style={fill}>
    <TopRow left="THEME · APPLIED" leftColor="#76C7C0" right="03 / 03" />

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
        把 <Accent>主题</Accent> 当 <Accent>设计语言</Accent>,<br />
        不当 装饰。
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
        copy theme/dark-teal.md · build your own slide
      </p>
    </div>

    <BottomRow left="Theme demo · end" right="VISUAL-DECK 1.0" />
  </div>
);

export default [Cover, Content, Closer];
