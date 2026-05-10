import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "exec_mysql_sql.py"
SPEC = importlib.util.spec_from_file_location("exec_mysql_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ExecMysqlSqlTests(unittest.TestCase):
    def test_load_env_file_parses_key_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env.local"
            env_path.write_text(
                "# comment\n"
                "MYSQL_HOST=localhost\n"
                "MYSQL_PORT=3306\n"
                "MYSQL_USER=test_user\n"
                "MYSQL_PASSWORD=test_password\n"
                "MYSQL_DATABASE=Xiangwang\n"
            )

            config = MODULE.load_env_file(env_path)

        self.assertEqual(config["MYSQL_HOST"], "localhost")
        self.assertEqual(config["MYSQL_PORT"], "3306")
        self.assertEqual(config["MYSQL_USER"], "test_user")
        self.assertEqual(config["MYSQL_PASSWORD"], "test_password")
        self.assertEqual(config["MYSQL_DATABASE"], "Xiangwang")

    @mock.patch("subprocess.run")
    def test_main_reads_stdin_and_executes_mysql_with_env_file(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env.local"
            env_path.write_text(
                "MYSQL_HOST=localhost\n"
                "MYSQL_PORT=3306\n"
                "MYSQL_USER=test_user\n"
                "MYSQL_PASSWORD=test_password\n"
                "MYSQL_DATABASE=Xiangwang\n"
            )
            stdin = io.StringIO("SELECT 1;")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
                exit_code = MODULE.main(["--env-file", str(env_path)])

        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args.kwargs["input"], "SELECT 1;")
        self.assertEqual(mock_run.call_args.kwargs["env"]["MYSQL_PWD"], "test_password")
        self.assertIn("--host=localhost", mock_run.call_args.args[0])
        self.assertIn("--port=3306", mock_run.call_args.args[0])
        self.assertIn("--user=test_user", mock_run.call_args.args[0])
        self.assertIn("Xiangwang", mock_run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
