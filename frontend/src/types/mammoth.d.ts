declare module 'mammoth' {
  interface ConvertToHtmlOptions {
    arrayBuffer?: ArrayBuffer;
    path?: string;
    buffer?: Buffer;
  }

  interface ConvertToHtmlResult {
    value: string;
    messages: Array<{
      type: string;
      message: string;
    }>;
  }

  interface ConvertToMarkdownOptions {
    arrayBuffer?: ArrayBuffer;
    path?: string;
    buffer?: Buffer;
  }

  interface ConvertToMarkdownResult {
    value: string;
    messages: Array<{
      type: string;
      message: string;
    }>;
  }

  export function convertToHtml(options: ConvertToHtmlOptions): Promise<ConvertToHtmlResult>;
  export function convertToMarkdown(options: ConvertToMarkdownOptions): Promise<ConvertToMarkdownResult>;
}
