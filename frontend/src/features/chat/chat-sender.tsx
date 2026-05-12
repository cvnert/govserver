import { useEffect, useState } from 'react'
import { Typography } from 'antd'
import { Sender } from '@ant-design/x'
import { useTranslation } from 'react-i18next'

type ChatSenderProps = {
  disabled?: boolean
  preset?: string | null
  onSubmit: (value: string) => Promise<void> | void
  dark: boolean
}

export function ChatSender({ disabled, preset, onSubmit, dark }: ChatSenderProps) {
  const [value, setValue] = useState('')
  const { t } = useTranslation()

  useEffect(() => {
    if (preset) {
      setValue(preset)
    }
  }, [preset])

  return (
    <div className="mx-auto w-full max-w-3xl">
      <Sender
        value={value}
        onChange={setValue}
        onSubmit={(next) => {
          setValue('')
          void onSubmit(next)
        }}
        loading={disabled}
        placeholder={t('senderPlaceholder')}
        autoSize={{ minRows: 1, maxRows: 6 }}
        className={`gov-sender ${dark ? 'gov-sender-dark' : 'gov-sender-light'}`}
      />
      <Typography.Text className={dark ? 'mt-2 block text-center text-xs !text-[#8c8c8c]' : 'mt-2 block text-center text-xs !text-[#6b7280]'}>
        {t('senderHint')}
      </Typography.Text>
    </div>
  )
}
